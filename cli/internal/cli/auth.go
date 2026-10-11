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
	"golang.org/x/oauth2"

	"github.com/datapointchris/ichrisbirch/cli/internal/config"
)

// loginTimeout is a backstop only — the device code carries its own expiry and
// the poll stops there first.
const loginTimeout = 15 * time.Minute

func newAuthCommand() *cobra.Command {
	cmd := asNamespace(&cobra.Command{
		Use:   "auth",
		Short: "Log in and out of the ichrisbirch API",
		Long: "Authenticate this machine against the identity provider using the OAuth 2.0\n" +
			"device authorization grant. The CLI prints a code and a URL; approve it in\n" +
			"any browser on any device, including from a different machine over SSH. The\n" +
			"resulting token is stored in the OS keychain, or in a file only this user\n" +
			"can read where there is none.\n\n" +
			"Where icb is pointed comes from one config file. `icb auth status` prints\n" +
			"its path and its api, issuer and client_id, and `icb auth login <url>` fills\n" +
			"in whatever it lacks.\n\n" +
			"With ICB_CLIENT_SECRET set, icb authenticates as the service client the\n" +
			"config file's client_id names, through the client-credentials grant. It\n" +
			"requests a token per run and stores nothing, so login and logout refuse.",
	})
	cmd.AddCommand(withAPIFlag(newAuthLoginCommand()), newAuthLogoutCommand(), withAPIFlag(newAuthStatusCommand()), withAPIFlag(newAuthTokenCommand()))
	return cmd
}

func newAuthLoginCommand() *cobra.Command {
	var clientID string
	cmd := &cobra.Command{
		Use:   "login [url]",
		Short: "Log in by approving a code in any browser",
		Long: "Log in to the API at url, or to the config file's api when url is omitted.\n" +
			"Whatever the file lacks is filled in: api from url, the issuer from the\n" +
			"API's RFC 9728 metadata, and the client id from --client-id or this\n" +
			"machine's short hostname. Each is printed with where it came from before\n" +
			"the login starts, and written to the file once it succeeds. A value already\n" +
			"in the file is never rewritten.",
		Example: "  icb auth login\n" +
			"  icb auth login https://ichrisbirch.com/api",
		Args: usageArgs(cobra.MaximumNArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if config.IsService() {
				return fmt.Errorf("%s is set, so icb authenticates as a service client with no login; unset it to log in as a person", config.ClientSecretEnv)
			}
			url := apiOverride
			if len(args) == 1 {
				if apiOverride != "" && apiOverride != args[0] {
					return usageError{fmt.Errorf("--api %s and the url %s name different APIs; give one", apiOverride, args[0])}
				}
				url = args[0]
			}

			ctx, cancel := context.WithTimeout(cmd.Context(), loginTimeout)
			defer cancel()

			deployment, err := config.ForLogin(ctx, url, clientID)
			if err != nil {
				return err
			}
			_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Logging in to:")
			goclilogin.WriteDeployment(cmd.ErrOrStderr(), deployment)
			_, _ = fmt.Fprintln(cmd.ErrOrStderr())

			login := config.Login(deployment)
			store := goclilogin.NewTokenStore(login)

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
			backend, err := store.Save(login.ClientID, token)
			if err != nil {
				return fmt.Errorf("save token: %w", err)
			}
			if backend == goclilogin.BackendFile {
				_, _ = fmt.Fprintf(cmd.ErrOrStderr(),
					"\nNo OS keyring on this host — the token is in %s, readable by this user only.\n",
					store.FilePath())
			}
			if err := deployment.Save(); err != nil {
				return fmt.Errorf("logged in as %s, but the config file was not written: %w", login.ClientID, err)
			}

			_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "\n✓ Logged in (%s)\n", login.ClientID)
			return nil
		},
	}
	cmd.Flags().StringVar(&clientID, "client-id", "",
		"Log in as this OAuth client when the config file names none (default icb-cli-<short hostname>)")
	return cmd
}

func newAuthLogoutCommand() *cobra.Command {
	return &cobra.Command{
		Use:     "logout",
		Short:   "Remove the stored token from this machine's keychain",
		Example: "  icb auth logout",
		Args:    noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			if config.IsService() {
				return fmt.Errorf("%s is set, so icb authenticates as a service client and stores no token to remove; unset it to log out as a person", config.ClientSecretEnv)
			}
			// Only the client id finds the token, so a file lacking the other
			// two keys still logs out. A file naming no client falls back to
			// icb-cli-<short hostname>, the id login uses when the file names
			// none, so a token stored by a login whose file was never written
			// is still removed. No other API is asked, so logout takes no --api.
			deployment, err := config.Load(cmd.Context(), "")
			if err != nil && !errors.Is(err, goclilogin.ErrNotConfigured) {
				return err
			}
			if deployment.ClientID.Value == "" {
				deployment.ClientID.Value = config.DefaultClientID()
			}
			clientID := deployment.ClientID.Value
			if err := goclilogin.NewTokenStore(config.Login(deployment)).Delete(clientID); err != nil {
				if errors.Is(err, goclilogin.ErrNotLoggedIn) {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Not logged in — nothing to remove.")
					return nil
				}
				return fmt.Errorf("remove token from keychain: %w", err)
			}
			_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "Logged out (%s).\n", clientID)
			return nil
		},
	}
}

func newAuthTokenCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "token",
		Short: "Print the current access token to stdout",
		Long: "Print a valid access token to stdout, refreshing it first if it has\n" +
			"expired. Intended for scripting. Pass it to curl on stdin, as the example\n" +
			"does, so the token never appears in another process's arguments. Exits\n" +
			"non-zero if not logged in. With ICB_CLIENT_SECRET set, it requests a new\n" +
			"service token instead.",
		Example: "  icb auth token\n" +
			"  printf 'Authorization: Bearer %s\\n' \"$(icb auth token)\" | curl --header @- https://ichrisbirch.com/api/tasks/",
		Args: noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			deployment, err := config.Load(cmd.Context(), apiOverride)
			if err != nil {
				return err
			}
			source, err := tokenSource(cmd.Context(), deployment)
			if errors.Is(err, errNeedsLogin) {
				_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "Not logged in as %s. Run `icb auth login`.\n", deployment.ClientID.Value)
				return exitCode(1)
			}
			if err != nil {
				return err
			}
			token, err := source.Token()
			if err != nil && config.IsService() {
				return fmt.Errorf("obtain a token for service client %s: %w", deployment.ClientID.Value, err)
			}
			if err != nil {
				return fmt.Errorf("obtain a valid token (refresh may have failed — try `icb auth login`): %w", err)
			}
			_, _ = fmt.Fprintln(cmd.OutOrStdout(), token.AccessToken)
			return nil
		},
	}
}

// credentialType is whose credential `auth status` checked, spelled as Google's
// credential files spell a person's OAuth login and a service's.
type credentialType string

const (
	// authorizedUser is the device-grant login a person made on this machine.
	authorizedUser credentialType = "authorized_user"
	// serviceAccount is the client-credentials grant ICB_CLIENT_SECRET selects.
	serviceAccount credentialType = "service_account"
)

// statusReport is the stable JSON schema for `auth status --json`. It reports
// what this machine holds, not what the token asserts: the claims are the API's
// to verify against Authelia's JWKS, and a local reading of them would only say
// what an unverified token claims about itself.
//
// For a service, logged_in is true only when the provider granted a token just
// now. A service stores none, so nothing else says the next command will work.
type statusReport struct {
	LoggedIn bool `json:"logged_in"`
	// Configured is false when the config file lacks a value, which ConfigFile
	// names and the empty fields below show.
	Configured bool                    `json:"configured"`
	ConfigFile string                  `json:"config_file"`
	Type       credentialType          `json:"type"`
	API        string                  `json:"api"`
	ClientID   string                  `json:"client_id"`
	Issuer     string                  `json:"issuer"`
	ExpiresAt  string                  `json:"expires_at,omitempty"`
	Expired    bool                    `json:"expired"`
	Session    goclilogin.SessionState `json:"session"`

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
		Use:   "status",
		Short: "Show where the CLI is pointed and whether it is logged in",
		Long: "Show the api, issuer and client_id this machine uses, where each came\n" +
			"from, the config file's path, and whether a token is stored for the client.\n" +
			"Exits 1 when the file lacks a value, no token is stored, or the provider\n" +
			"rejected the session.",
		Example: "  icb auth status\n  icb auth status --json",
		Args:    noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			deployment, loadErr := config.Load(cmd.Context(), apiOverride)
			if loadErr != nil && !errors.Is(loadErr, goclilogin.ErrNotConfigured) {
				return loadErr
			}
			report := statusReport{
				Configured: loadErr == nil,
				ConfigFile: deployment.Path,
				Type:       authorizedUser,
				API:        deployment.API.Value,
				ClientID:   deployment.ClientID.Value,
				Issuer:     deployment.Issuer.Value,
			}
			if config.IsService() {
				report.Type = serviceAccount
			}
			switch {
			case !report.Configured:
			case config.IsService():
				serviceStatus(cmd.Context(), deployment, &report)
			default:
				if err := loginStatus(cmd.Context(), deployment, &report); err != nil {
					return err
				}
			}

			if asJSON {
				enc := json.NewEncoder(cmd.OutOrStdout())
				enc.SetIndent("", "  ")
				if err := enc.Encode(report); err != nil {
					return err
				}
			} else {
				printStatus(cmd.OutOrStdout(), report, deployment, loadErr)
			}

			// A rejected session exits non-zero for the same reason being logged
			// out does: nothing the caller runs next will work until they log in.
			// An unverified login exits zero, because its stored token may still
			// work. An unverified service exits 1 through logged_in, which
			// serviceStatus sets only for a live session.
			if !report.Configured || !report.LoggedIn || report.Session == goclilogin.SessionRejected {
				return exitCode(1)
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output status as JSON to stdout")
	return cmd
}

// loginStatus fills report from the token this machine logged in for.
func loginStatus(ctx context.Context, d goclilogin.Deployment, report *statusReport) error {
	login := config.Login(d)
	store := goclilogin.NewTokenStore(login)
	token, backend, err := store.Load(d.ClientID.Value)
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
		report.Session, token = goclilogin.VerifySession(ctx, login, store)
		if token != nil && !token.Expiry.IsZero() {
			report.ExpiresAt = token.Expiry.Format(time.RFC3339)
			report.Expired = time.Now().After(token.Expiry)
		}
	}
	return nil
}

// serviceStatus requests a token, because a service stores none that could say
// whether its credentials still work.
func serviceStatus(ctx context.Context, d goclilogin.Deployment, report *statusReport) {
	source, err := goclilogin.ClientCredentialsTokenSource(ctx, config.Service(d), config.ClientSecret())
	var token *oauth2.Token
	if err == nil {
		token, err = source.Token()
	}
	report.Session, token = goclilogin.ClassifySession(token, err)
	report.LoggedIn = report.Session == goclilogin.SessionLive
	if token != nil && !token.Expiry.IsZero() {
		report.ExpiresAt = token.Expiry.Format(time.RFC3339)
	}
}

// printStatus leads with the verdict on a line of its own, then prints where
// the CLI is pointed. A script checking a login reads the first line alone.
//
// WriteDeployment's widest key is client_id, padded by two, so the rows after
// it pad their key to the column its values start in.
func printStatus(out io.Writer, r statusReport, d goclilogin.Deployment, loadErr error) {
	switch {
	case !r.Configured:
		_, _ = fmt.Fprintf(out, "%v\n", loadErr)
	case r.Type == serviceAccount && r.Session == goclilogin.SessionRejected:
		_, _ = fmt.Fprintf(out, "Service client refused by %s. Check client_id in the config file, and %s.\n", r.Issuer, config.ClientSecretEnv)
	case r.Type == serviceAccount && r.Session == goclilogin.SessionUnverified:
		_, _ = fmt.Fprintf(out, "Service client configured; %s could not be reached.\n", r.Issuer)
	case r.Type == serviceAccount:
		_, _ = fmt.Fprintln(out, "Service client (client credentials)")
	case !r.LoggedIn:
		_, _ = fmt.Fprintf(out, "Not logged in as %s. Run `icb auth login` to authenticate.\n", r.ClientID)
	case r.Session == goclilogin.SessionRejected:
		_, _ = fmt.Fprintf(out, "Session rejected by %s. Run `icb auth login` to authenticate.\n", r.Issuer)
	default:
		_, _ = fmt.Fprintln(out, "Logged in")
	}
	goclilogin.WriteDeployment(out, d)
	if r.KeyringNote != "" {
		_, _ = fmt.Fprintf(out, "  %-11s%s\n", "note", r.KeyringNote)
	}
	if r.ExpiresAt != "" {
		state := "valid"
		switch {
		case r.Type == serviceAccount:
			state = "granted"
		case r.Expired:
			state = "expired — will refresh on next use"
		}
		_, _ = fmt.Fprintf(out, "  %-11s%s (expires %s)\n", "token", state, r.ExpiresAt)
	}
	if r.Backend == goclilogin.BackendFile {
		_, _ = fmt.Fprintf(out, "  %-11s%s — no OS keyring on this host\n", "storage", r.Backend)
	}
	if r.Type != serviceAccount && r.Session == goclilogin.SessionUnverified {
		_, _ = fmt.Fprintf(out, "  %-11sunverified — %s could not be reached\n", "session", r.Issuer)
	}
}
