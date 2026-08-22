package cli

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"time"

	"github.com/pkg/browser"
	"github.com/spf13/cobra"
	"golang.org/x/oauth2"

	"github.com/datapointchris/ichrisbirch/cli/internal/auth"
	"github.com/datapointchris/ichrisbirch/cli/internal/config"
)

// loginTimeout is a backstop only — the device code carries its own expiry and
// the poll stops there first.
const loginTimeout = 15 * time.Minute

func newAuthCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth",
		Short: "Log in and out of the ichrisbirch API",
		Long: "Authenticate this machine against Authelia using the OAuth 2.0 device\n" +
			"authorization grant. The CLI prints a code and a URL; approve it in any\n" +
			"browser on any device, including from a different machine over SSH. The\n" +
			"resulting token is stored in the OS keychain, never on disk.",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(newAuthLoginCommand(), newAuthLogoutCommand(), newAuthStatusCommand(), newAuthTokenCommand())
	return cmd
}

func newAuthLoginCommand() *cobra.Command {
	return &cobra.Command{
		Use:     "login",
		Short:   "Log in by approving a code in any browser",
		Example: "  icb auth login",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfg := config.Load()
			store := auth.NewTokenStore()

			ctx, cancel := context.WithTimeout(cmd.Context(), loginTimeout)
			defer cancel()

			// pkg/browser hands the launcher subprocess os.Stdout and os.Stderr,
			// which puts whatever the browser writes at startup — GPU warnings,
			// favicon decode failures, a dbus complaint — in the middle of the
			// user code and the verification URL. A launcher that fails is
			// reported by OpenURL's error instead, so nothing diagnostic is lost
			// by dropping the stream. Package-level vars are the library's only
			// knob for it.
			browser.Stdout = io.Discard
			browser.Stderr = io.Discard

			token, err := auth.Login(ctx, cfg, browser.OpenURL, cmd.ErrOrStderr())
			if err != nil {
				if errors.Is(err, context.DeadlineExceeded) {
					return fmt.Errorf("timed out waiting for approval after %s; run `icb auth login` again", loginTimeout)
				}
				return err
			}
			if err := store.Save(cfg.ClientID, token); err != nil {
				return fmt.Errorf("save token to keychain: %w", err)
			}

			_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "\n✓ Logged in (%s)\n", cfg.ClientID)
			return nil
		},
	}
}

func newAuthLogoutCommand() *cobra.Command {
	return &cobra.Command{
		Use:     "logout",
		Short:   "Remove the stored token from this machine's keychain",
		Example: "  icb auth logout",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfg := config.Load()
			store := auth.NewTokenStore()

			if err := store.Delete(cfg.ClientID); err != nil {
				if errors.Is(err, auth.ErrNotLoggedIn) {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Not logged in — nothing to remove.")
					return nil
				}
				return fmt.Errorf("remove token from keychain: %w", err)
			}
			_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "Logged out (%s).\n", cfg.ClientID)
			return nil
		},
	}
}

func newAuthTokenCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "token",
		Short: "Print the current access token to stdout",
		Long: "Print a valid access token to stdout, refreshing it first if it has\n" +
			"expired. Intended for scripting, e.g. `curl -H \"Authorization: Bearer\n" +
			"$(icb auth token)\" …`. Exits non-zero if not logged in.",
		Example: "  icb auth token",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfg := config.Load()
			store := auth.NewTokenStore()

			source, err := auth.TokenSource(cmd.Context(), cfg, store)
			if errors.Is(err, auth.ErrNotLoggedIn) {
				_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "Not logged in as %s. Run `icb auth login`.\n", cfg.ClientID)
				return exitCode(1)
			}
			if err != nil {
				return err
			}
			token, err := source.Token()
			if err != nil {
				return fmt.Errorf("obtain a valid token (refresh may have failed — try `icb auth login`): %w", err)
			}
			_, _ = fmt.Fprintln(cmd.OutOrStdout(), token.AccessToken)
			return nil
		},
	}
}

// statusReport is the stable JSON schema for `auth status --json`. It reports
// what this machine holds, not what the token asserts: the claims are the API's
// to verify against Authelia's JWKS, and a local reading of them would only say
// what an unverified token claims about itself.
type statusReport struct {
	LoggedIn  bool   `json:"logged_in"`
	ClientID  string `json:"client_id"`
	Issuer    string `json:"issuer"`
	ExpiresAt string `json:"expires_at,omitempty"`
	Expired   bool   `json:"expired"`
	Session   string `json:"session"`
}

// The three answers `session` carries. A stored token says only what this
// machine holds, and an expired access token is refreshed on the next call, so
// holding one is not the same as being able to use it: the refresh token behind
// it may have been revoked, and only the issuer knows.
const (
	sessionLive       = "live"       // a usable access token was obtained
	sessionRejected   = "rejected"   // the issuer refused the refresh; only a login fixes it
	sessionUnverified = "unverified" // the issuer could not be reached to ask
)

func newAuthStatusCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "status",
		Short:   "Show whether the CLI is logged in",
		Example: "  icb auth status\n  icb auth status --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfg := config.Load()
			store := auth.NewTokenStore()

			report := statusReport{ClientID: cfg.ClientID, Issuer: cfg.Issuer}

			token, err := store.Load(cfg.ClientID)
			switch {
			case errors.Is(err, auth.ErrNotLoggedIn):
				// logged out is a valid state, reported on stdout, exit 1 (like gh)
			case err != nil:
				return fmt.Errorf("read token from keychain: %w", err)
			default:
				report.LoggedIn = true
				if !token.Expiry.IsZero() {
					report.ExpiresAt = token.Expiry.Format(time.RFC3339)
					report.Expired = time.Now().After(token.Expiry)
				}
				// Ask for a token the way a resource command does, which is the
				// only thing that separates a soft expiry from a revoked grant.
				// A live access token answers locally; an expired one performs
				// the refresh the next call would have performed anyway, so the
				// answer costs nothing that was not already due.
				report.Session, token = verifySession(cmd.Context(), cfg, store)
				if token != nil && !token.Expiry.IsZero() {
					report.ExpiresAt = token.Expiry.Format(time.RFC3339)
					report.Expired = time.Now().After(token.Expiry)
				}
			}

			if asJSON {
				enc := json.NewEncoder(cmd.OutOrStdout())
				enc.SetIndent("", "  ")
				if err := enc.Encode(report); err != nil {
					return err
				}
			} else {
				printStatus(cmd, report)
			}

			// A rejected session exits non-zero for the same reason being logged
			// out does: nothing the caller runs next will work until they log in.
			// An unverified one exits zero, because nothing established it is bad.
			if !report.LoggedIn || report.Session == sessionRejected {
				return exitCode(1)
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output status as JSON to stdout")
	return cmd
}

// verifySession obtains a token through the same path a resource command uses
// and reports which of the three states the session is in, along with whatever
// token it ended up holding. A refusal at the token endpoint is the issuer
// saying the grant is gone; anything else is this machine failing to ask.
func verifySession(ctx context.Context, cfg config.Config, store *auth.TokenStore) (string, *oauth2.Token) {
	source, err := auth.TokenSource(ctx, cfg, store)
	if err != nil {
		return sessionUnverified, nil
	}
	return classifySession(source.Token())
}

// classifySession reads the outcome of asking for a token. A refusal at the
// token endpoint is the issuer saying the grant is gone, which only a login
// fixes; every other error is this machine failing to ask, which proves nothing
// about the grant and must not be reported as though it did.
func classifySession(token *oauth2.Token, err error) (string, *oauth2.Token) {
	if err == nil {
		return sessionLive, token
	}
	var retrieveErr *oauth2.RetrieveError
	if errors.As(err, &retrieveErr) {
		return sessionRejected, nil
	}
	return sessionUnverified, nil
}

func printStatus(cmd *cobra.Command, r statusReport) {
	out := cmd.OutOrStdout()
	if !r.LoggedIn {
		_, _ = fmt.Fprintf(out, "Not logged in as %s.\nRun `icb auth login` to authenticate.\n", r.ClientID)
		return
	}
	if r.Session == sessionRejected {
		_, _ = fmt.Fprintf(out, "Session rejected by %s.\nRun `icb auth login` to authenticate.\n", r.Issuer)
		_, _ = fmt.Fprintf(out, "  client:   %s\n", r.ClientID)
		return
	}
	_, _ = fmt.Fprintf(out, "Logged in\n")
	_, _ = fmt.Fprintf(out, "  client:   %s\n", r.ClientID)
	_, _ = fmt.Fprintf(out, "  issuer:   %s\n", r.Issuer)
	if r.ExpiresAt != "" {
		state := "valid"
		if r.Expired {
			state = "expired"
		}
		_, _ = fmt.Fprintf(out, "  token:    %s (expires %s)\n", state, r.ExpiresAt)
	}
	if r.Session == sessionUnverified {
		_, _ = fmt.Fprintf(out, "  session:  unverified — %s could not be reached\n", r.Issuer)
	}
}
