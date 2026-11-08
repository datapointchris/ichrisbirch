// Package config resolves the life CLI's settings and its state directory.
//
// Which deployment to talk to is one file, $XDG_CONFIG_HOME/life/config.toml,
// read through goclilogin's config-file contract: its api, issuer and
// client_id keys, with --api the only thing that outranks them. None of the
// three is compiled in. Each names one installation, so a value shipped in the
// binary would point somebody else's copy at this one.
package config

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/datapointchris/goclilogin"
)

// product names the config file's directory.
const product = "life"

// keyringService namespaces life's entries in the OS keychain. A stored token
// is found only under the name it was written with, so a new name means every
// machine logs in again.
const keyringService = "life-cli"

// The scope a service client requests, the one listing every read `life
// overview` makes. Authelia grants only the scopes a request names, so a
// request naming none gets a token the API refuses. It refuses the whole
// request when one names a scope the client does not hold.
// life/api/client_scopes.py lists the routes it reaches.
const serviceScope = "life.overview.read"

// ClientSecretEnv selects the client-credentials grant, for the client the
// config file names. It is read from the environment alone, so it is never
// written to the file and no command prints it.
const ClientSecretEnv = "LIFE_CLIENT_SECRET"

// Load reads the deployment every command talks to. api is the --api flag's
// value, and outranks the file's when it is not empty.
//
// A service missing a value is told which key to write rather than to log in,
// since a service has no login.
func Load(ctx context.Context, api string) (goclilogin.Deployment, error) {
	if err := refuseFormerName(); err != nil {
		return goclilogin.Deployment{}, err
	}
	d, err := goclilogin.LoadDeployment(ctx, product, api)
	if stale := refuseRetiredAPIPath(d.API); stale != nil {
		return d, stale
	}
	if d.HandsTokens() && IsService() {
		return d, fmt.Errorf("%s sets token_command and %s is set, so life has two credentials; keep one",
			d.Path, ClientSecretEnv)
	}
	if !IsService() || !errors.Is(err, goclilogin.ErrNotConfigured) {
		return d, err
	}
	var missing []string
	for _, key := range []struct {
		name string
		set  goclilogin.Setting
	}{{"api", d.API}, {"issuer", d.Issuer}, {"client_id", d.ClientID}} {
		if key.set.Value == "" {
			missing = append(missing, key.name)
		}
	}
	return d, fmt.Errorf("%w: %s sets no %s; a service names its API, provider and client there, and only %s in its environment",
		goclilogin.ErrNotConfigured, d.Path, strings.Join(missing, " or "), ClientSecretEnv)
}

// ForLogin is the deployment `life auth login` logs in to: the file's values,
// with whatever it lacks filled in from api, the API's metadata and clientID.
func ForLogin(ctx context.Context, api, clientID string) (goclilogin.Deployment, error) {
	if err := refuseFormerName(); err != nil {
		return goclilogin.Deployment{}, err
	}
	if err := refuseRetiredAPIPath(goclilogin.Setting{Value: api, Source: goclilogin.SourceCommandLine}); err != nil {
		return goclilogin.Deployment{}, err
	}
	d, err := goclilogin.DeploymentForLogin(ctx, product, api, clientID)
	if stale := refuseRetiredAPIPath(d.API); stale != nil {
		return d, stale
	}
	return d, err
}

// retiredAPIPath is where api ended while a proxy stripped it in front of an
// API serving its routes at the root. The client adds /api/v1 to api, so one
// still ending in /api reaches /api/api/v1.
const retiredAPIPath = "/api"

// refuseRetiredAPIPath names the line to change, because login never rewrites
// a value the file already holds. It wraps ErrNotConfigured, so config show
// and auth status still print the file, and logout still removes the token.
func refuseRetiredAPIPath(api goclilogin.Setting) error {
	u, err := url.Parse(api.Value)
	if err != nil || strings.TrimRight(u.Path, "/") != retiredAPIPath {
		return nil
	}
	host := (&url.URL{Scheme: u.Scheme, Host: u.Host}).String()
	if api.Source == goclilogin.SourceFile {
		return fmt.Errorf("%w: %s sets api = %q, and life adds /api/v1 to it; change that line to api = %q",
			goclilogin.ErrNotConfigured, api.From, api.Value, host)
	}
	return fmt.Errorf("%w: %s ends in /api, and life adds /api/v1 to it; name the host alone, %s",
		goclilogin.ErrNotConfigured, api.Value, host)
}

// Path is where the deployment file goes, whether or not it exists.
func Path() string { return goclilogin.ConfigPath(product) }

// DefaultClientID is the client id login derives when neither the file nor
// --client-id names one: life-cli-<short hostname>.
func DefaultClientID() string { return goclilogin.ClientID(product) }

// Login is the goclilogin view of a deployment: which provider to authenticate
// against, as which client, and where the token and its refresh lock live.
//
// StateDir is passed rather than left to goclilogin's default, which would put
// it under the keyring service name. Naming life's own state directory ties the
// lock's path to the product name, so two versions running during an upgrade
// contend for the same file rather than each taking its own.
func Login(d goclilogin.Deployment) goclilogin.Config {
	return goclilogin.Config{
		Issuer:         d.Issuer.Value,
		ClientID:       d.ClientID.Value,
		KeyringService: keyringService,
		StateDir:       StatePath(),
	}
}

// ClientSecret is LIFE_CLIENT_SECRET, set only where a service runs life with
// nobody present to approve a device login.
func ClientSecret() string { return os.Getenv(ClientSecretEnv) }

// IsService reports whether life authenticates as a confidential service client
// rather than as the person who logged in on this machine.
func IsService() bool { return ClientSecret() != "" }

// Service is the goclilogin view of a deployment for the client-credentials
// grant. Nothing it obtains is stored, so it names no keyring or state
// directory.
func Service(d goclilogin.Deployment) goclilogin.ServiceClient {
	return goclilogin.ServiceClient{Issuer: d.Issuer.Value, ClientID: d.ClientID.Value, Scopes: []string{serviceScope}}
}

// StatePath resolves a path under life's own XDG state directory —
// $XDG_STATE_HOME/life, falling back to ~/.local/state/life. State is what the
// tool writes and the user does not, such as goclilogin's refresh lock. Returns
// "" when the home directory cannot be resolved, which callers treat as "no
// state directory available" rather than as an error.
func StatePath(parts ...string) string {
	base := os.Getenv("XDG_STATE_HOME")
	if base == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return ""
		}
		base = filepath.Join(home, ".local", "state")
	}
	return filepath.Join(append([]string{base, "life"}, parts...)...)
}
