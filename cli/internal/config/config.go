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
	"strings"
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

// Scopes requested at login. offline_access yields the refresh token; openid
// and profile make the access token a standard OIDC one. The bearer.authz
// scope is deliberately absent — Authelia permits only authorization_code,
// refresh_token and client_credentials alongside it, which rules out the
// device grant this CLI logs in with.
var Scopes = []string{"openid", "profile", "offline_access"}

type Config struct {
	Issuer   string
	ClientID string
	APIBase  string
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
	host, err := os.Hostname()
	if err != nil || host == "" {
		return "icb-cli"
	}
	short := strings.ToLower(strings.SplitN(host, ".", 2)[0])
	return "icb-cli-" + short
}

func getEnv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		return v
	}
	return fallback
}
