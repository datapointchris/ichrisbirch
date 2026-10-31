// Package config resolves the icb CLI's settings, of which there are two kinds.
//
// Which deployment to talk to is one file, $XDG_CONFIG_HOME/icb/config.toml,
// read through goclilogin's config-file contract: its api, issuer and
// client_id keys, with --api the only thing that outranks them. None of the
// three is compiled in. Each names one installation, so a value shipped in the
// binary would point somebody else's copy at this one.
//
// MachineConfig is what this machine says about its own layout, read from
// config.yml beside it. It is the middle rung of the order every shared path
// resolves through: the ICB_-prefixed variable, then the config key, then a
// default under icb's own XDG directory.
package config

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"os"
	"strings"

	"github.com/datapointchris/goclilogin"
)

// product names the config file's directory.
const product = "icb"

// keyringService namespaces icb's entries in the OS keychain. It is a deployed
// identifier rather than a path-derived one, so it keeps its spelling
// independently of the module or binary name.
const keyringService = "icb-cli"

// The scopes a service client requests. Authelia grants only the scopes a
// request names, so a request naming none gets a token the API refuses. It
// refuses the whole request when one names a scope the client does not hold.
// ichrisbirch/api/client_scopes.py lists the routes each one reaches.
const (
	projectItemsScope = "icb.project-items.read"
	issuesScope       = "icb.issues.read"
	issuesClaimScope  = "icb.issues.claim"
	issuesCloseScope  = "icb.issues.close"
	issuesPlanScope   = "icb.issues.plan"
)

// ClientSecretEnv selects the client-credentials grant, for the client the
// config file names. It is read from the environment alone, so it is never
// written to the file and no command prints it.
const ClientSecretEnv = "ICB_CLIENT_SECRET"

// Load reads the deployment every command talks to. api is the --api flag's
// value, and outranks the file's when it is not empty.
//
// A service missing a value is told which key to write rather than to log in,
// since a service has no login.
func Load(ctx context.Context, api string) (goclilogin.Deployment, error) {
	if err := refuseRetiredAPIBase(); err != nil {
		return goclilogin.Deployment{}, err
	}
	d, err := goclilogin.LoadDeployment(ctx, product, api)
	if stale := refuseRetiredAPIPath(d.API); stale != nil {
		return d, stale
	}
	if d.HandsTokens() && IsService() {
		return d, fmt.Errorf("%s sets token_command and %s is set, so icb has two credentials; keep one",
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

// ForLogin is the deployment `icb auth login` logs in to: the file's values,
// with whatever it lacks filled in from api, the API's metadata and clientID.
func ForLogin(ctx context.Context, api, clientID string) (goclilogin.Deployment, error) {
	if err := refuseRetiredAPIBase(); err != nil {
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
		return fmt.Errorf("%w: %s sets api = %q, and icb adds /api/v1 to it; change that line to api = %q",
			goclilogin.ErrNotConfigured, api.From, api.Value, host)
	}
	return fmt.Errorf("%w: %s ends in /api, and icb adds /api/v1 to it; name the host alone, %s",
		goclilogin.ErrNotConfigured, api.Value, host)
}

// retiredAPIBase is how earlier releases were pointed at another API, dev
// among them. One still set is refused rather than ignored, because ignoring it
// sends a command meant for dev to the config file's API, which is production.
//
// ICB_CLIENT_ID is not refused: a service's environment carries it until the
// service runs a release that reads client_id from the file instead.
const retiredAPIBase = "ICB_API_BASE"

func refuseRetiredAPIBase() error {
	if os.Getenv(retiredAPIBase) == "" {
		return nil
	}
	return fmt.Errorf("%s is set, and icb no longer reads it: pass --api to point one command at another API, or unset it to use the config file's api", retiredAPIBase)
}

// Path is where the deployment file goes, whether or not it exists.
func Path() string { return goclilogin.ConfigPath(product) }

// DefaultClientID is the client id login derives when neither the file nor
// --client-id names one: icb-cli-<short hostname>.
func DefaultClientID() string { return goclilogin.ClientID(product) }

// Login is the goclilogin view of a deployment: which provider to authenticate
// against, as which client, and where the token and its refresh lock live.
//
// StateDir is passed rather than left to goclilogin's default, which would put
// it under the keyring service name. Naming icb's own state directory keeps the
// lock where earlier versions wrote it, so two versions running during an
// upgrade contend for the same file rather than each taking its own.
func Login(d goclilogin.Deployment) goclilogin.Config {
	return goclilogin.Config{
		Issuer:         d.Issuer.Value,
		ClientID:       d.ClientID.Value,
		KeyringService: keyringService,
		StateDir:       StatePath(),
	}
}

// ClientSecret is ICB_CLIENT_SECRET, set only where a service runs icb with
// nobody present to approve a device login.
func ClientSecret() string { return os.Getenv(ClientSecretEnv) }

// IsService reports whether icb authenticates as a confidential service client
// rather than as the person who logged in on this machine.
func IsService() bool { return ClientSecret() != "" }

// Service is the goclilogin view of a deployment for the client-credentials
// grant. Nothing it obtains is stored, so it names no keyring or state
// directory.
func Service(d goclilogin.Deployment) goclilogin.ServiceClient {
	return goclilogin.ServiceClient{Issuer: d.Issuer.Value, ClientID: d.ClientID.Value, Scopes: []string{projectItemsScope, issuesScope, issuesClaimScope, issuesCloseScope, issuesPlanScope}}
}
