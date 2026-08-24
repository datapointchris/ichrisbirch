package cli

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/datapointchris/goclilogin"
	"github.com/pkg/browser"
	"github.com/spf13/cobra"

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
			login := cfg.Login()
			store := goclilogin.NewTokenStore(login)

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

			token, err := goclilogin.Login(ctx, login, func(p goclilogin.DevicePrompt) {
				goclilogin.WriteInstructions(cmd.ErrOrStderr(), login.ClientID, p)
				if openErr := browser.OpenURL(p.BrowserURL()); openErr != nil {
					_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "(could not open a browser here: %v)\n", openErr)
				}
			})
			if err != nil {
				if errors.Is(err, context.DeadlineExceeded) {
					return fmt.Errorf("timed out waiting for approval after %s; run `icb auth login` again", loginTimeout)
				}
				return err
			}
			backend, err := store.Save(cfg.ClientID, token)
			if err != nil {
				return fmt.Errorf("save token: %w", err)
			}
			if backend == goclilogin.BackendFile {
				_, _ = fmt.Fprintf(cmd.ErrOrStderr(),
					"\nNo OS keyring on this host — the token is in %s, readable by this user only.\n",
					store.FilePath())
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
			store := goclilogin.NewTokenStore(cfg.Login())

			if err := store.Delete(cfg.ClientID); err != nil {
				if errors.Is(err, goclilogin.ErrNotLoggedIn) {
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
			store := goclilogin.NewTokenStore(cfg.Login())

			source, err := goclilogin.TokenSource(cmd.Context(), cfg.Login(), store)
			if errors.Is(err, goclilogin.ErrNotLoggedIn) {
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
	LoggedIn  bool                    `json:"logged_in"`
	ClientID  string                  `json:"client_id"`
	Issuer    string                  `json:"issuer"`
	ExpiresAt string                  `json:"expires_at,omitempty"`
	Expired   bool                    `json:"expired"`
	Session   goclilogin.SessionState `json:"session"`

	// Backend is where the token is kept. A host with no OS keyring stores it
	// in a mode-600 file instead, and that is worth saying out loud.
	Backend goclilogin.Backend `json:"backend,omitempty"`

	// KeyringNote carries the keyring's own failure when there is no token and
	// the keyring is the reason, rather than simply holding no entry.
	KeyringNote string `json:"keyring_note,omitempty"`
}

func newAuthStatusCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "status",
		Short:   "Show whether the CLI is logged in",
		Example: "  icb auth status\n  icb auth status --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			cfg := config.Load()
			store := goclilogin.NewTokenStore(cfg.Login())

			report := statusReport{ClientID: cfg.ClientID, Issuer: cfg.Issuer}

			token, backend, err := store.Load(cfg.ClientID)
			switch {
			case errors.Is(err, goclilogin.ErrNotLoggedIn):
				// Logged out is a valid state, reported on stdout, exit 1 (like gh).
				// goclilogin wraps ErrNotLoggedIn with the keyring's own failure when
				// there was one, and that distinction decides what the user should do:
				// a host with no Secret Service is fixed by logging in, a locked
				// keychain is not.
				if detail := strings.TrimPrefix(err.Error(), goclilogin.ErrNotLoggedIn.Error()); detail != "" {
					report.KeyringNote = strings.Trim(detail, " ()")
				}
			case err != nil:
				return fmt.Errorf("read token from keychain: %w", err)
			default:
				report.LoggedIn = true
				report.Backend = backend
				if !token.Expiry.IsZero() {
					report.ExpiresAt = token.Expiry.Format(time.RFC3339)
					report.Expired = time.Now().After(token.Expiry)
				}
				// Ask for a token the way a resource command does, which is the
				// only thing that separates a soft expiry from a revoked grant.
				// A live access token answers locally; an expired one performs
				// the refresh the next call would have performed anyway, so the
				// answer costs nothing that was not already due.
				report.Session, token = goclilogin.VerifySession(cmd.Context(), cfg.Login(), store)
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
			if !report.LoggedIn || report.Session == goclilogin.SessionRejected {
				return exitCode(1)
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output status as JSON to stdout")
	return cmd
}

func printStatus(cmd *cobra.Command, r statusReport) {
	out := cmd.OutOrStdout()
	if !r.LoggedIn {
		_, _ = fmt.Fprintf(out, "Not logged in as %s.\nRun `icb auth login` to authenticate.\n", r.ClientID)
		if r.KeyringNote != "" {
			_, _ = fmt.Fprintf(out, "  note:     %s\n", r.KeyringNote)
		}
		return
	}
	if r.Session == goclilogin.SessionRejected {
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
	if r.Backend == goclilogin.BackendFile {
		_, _ = fmt.Fprintf(out, "  storage:  %s — no OS keyring on this host\n", r.Backend)
	}
	if r.Session == goclilogin.SessionUnverified {
		_, _ = fmt.Fprintf(out, "  session:  unverified — %s could not be reached\n", r.Issuer)
	}
}
