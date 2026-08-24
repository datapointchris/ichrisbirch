// Package config resolves the icb CLI's settings, of which there are two kinds.
//
// Config is which deployment to talk to — OIDC and API settings, environment
// overrides layered over homelab defaults. MachineConfig is what this machine
// says about its own layout, read from a config file, and it is the middle rung
// of the order every shared path resolves through: the ICB_-prefixed variable,
// then the config key, then a default under icb's own XDG directory.
package config

import (
	"os"

	"github.com/datapointchris/goclilogin"
)

const (
	defaultIssuer = "https://auth.ichrisbirch.com"
	// The `ichrisbirch-bearer` Traefik router carries a request holding an
	// Authorization header straight to the app without meeting ForwardAuth, so
	// this host serves the CLI without the bearer.authz scope the edge would
	// otherwise demand. Deliberately not api.ichrisbirch.com: that host bypasses
	// ForwardAuth for every request rather than only bearer ones, and it is
	// being retired along with the Personal API Key clients it was built for.
	defaultAPIBase = "https://ichrisbirch.com/api"
)

// keyringService namespaces icb's entries in the OS keychain. It is a deployed
// identifier rather than a path-derived one, so it keeps its spelling
// independently of the module or binary name.
const keyringService = "icb-cli"

type Config struct {
	Issuer   string
	ClientID string
	APIBase  string
}

// Login is the goclilogin view of this config: which provider to authenticate
// against, as which client, and where the token and its refresh lock live.
//
// StateDir is passed rather than left to goclilogin's default, which would put
// it under the keyring service name. Naming icb's own state directory keeps the
// lock where earlier versions wrote it, so two versions running during an
// upgrade contend for the same file rather than each taking its own.
func (c Config) Login() goclilogin.Config {
	return goclilogin.Config{
		Issuer:         c.Issuer,
		ClientID:       c.ClientID,
		KeyringService: keyringService,
		StateDir:       StatePath(),
	}
}

// Load resolves settings. Precedence per CLI conventions: env var > default.
// A config file layer can slot in below env later without changing callers.
func Load() Config {
	return Config{
		Issuer:   getEnv("ICB_OIDC_ISSUER", defaultIssuer),
		ClientID: getEnv("ICB_CLIENT_ID", defaultClientID()),
		APIBase:  getEnv("ICB_API_BASE", defaultAPIBase),
	}
}

// defaultClientID derives the per-(machine × app) Authelia client_id from the
// short hostname: `macmini.trusted` → `icb-cli-macmini`, matching the clients
// registered in the Authelia template. Machines whose hostname differs from
// their logical name override with ICB_CLIENT_ID (pyinfra can template this).
func defaultClientID() string {
	return goclilogin.ClientID("icb")
}

func getEnv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		return v
	}
	return fallback
}
