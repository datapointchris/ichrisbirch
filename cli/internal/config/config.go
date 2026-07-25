// Package config resolves the icb CLI's OIDC and API settings from environment
// overrides layered over homelab defaults.
package config

import (
	"os"
	"strings"
)

const (
	defaultIssuer = "https://auth.ichrisbirch.com"
	// defaultAudience / defaultAPIBase target the cookie-gated ichrisbirch.com
	// webapp host — the same nomad-consistent single-domain model where nomad-cli
	// targets nomad.ichrisbirch.com. That host is already Authelia ForwardAuth
	// protected and content-negotiates cookie (browser) vs bearer (this CLI), so
	// icb's opaque `authelia.bearer.authz` token is edge-validated by audience and
	// Remote-User is injected — the FastAPI's highest-priority auth path. The app's
	// internal Traefik strips the /api prefix before the request reaches FastAPI.
	// Deliberately NOT api.ichrisbirch.com: that host *bypasses* ForwardAuth for
	// direct Personal API Key / JWT clients, so routing here needs no Traefik change
	// and left the MCP's bypass untouched through its retirement. Both are
	// env-overridable.
	defaultAudience = "https://ichrisbirch.com"
	defaultAPIBase  = "https://ichrisbirch.com/api"
)

// LoopbackPorts is the fixed set registered as redirect_uris on the Authelia
// icb-cli clients (RFC 8252 §7.3 avoidance — Authelia matches exact URIs, so we
// register a small set and bind the first free one). Distinct from nomad's
// 8250-8252 and meso's 8260-8262 so a login for one app never contends with a
// login for another for a port.
var LoopbackPorts = []int{8270, 8271, 8272}

// RedirectHost is the hostname used in the loopback redirect_uri, matching a
// registered redirect_uri on the Authelia clients (both `localhost` and
// `127.0.0.1` spellings are registered). Safari shows an https→http
// insecure-form warning on the form_post callback regardless of spelling
// (verified 2026-07-23 — `localhost` did not suppress it), so we use the IP
// literal. The warning is accepted; the 90-day refresh token (Authelia `cli`
// lifespan) makes an interactive login a ~quarterly event, so it is rare.
const RedirectHost = "127.0.0.1"

// Scopes requested at login. authelia.bearer.authz is Authelia's native bearer
// authorization scope — the resulting access token is opaque and authorized at
// the Traefik ForwardAuth edge by audience. offline_access yields a refresh
// token. No openid/profile: there is no id_token and identity is not read from
// the token (it is edge-authorized), so those scopes would be dead weight.
var Scopes = []string{"authelia.bearer.authz", "offline_access"}

type Config struct {
	Issuer   string
	ClientID string
	Audience string
	APIBase  string
}

// Load resolves settings. Precedence per CLI conventions: env var > default.
// A config file layer can slot in below env later without changing callers.
func Load() Config {
	return Config{
		Issuer:   getEnv("ICB_OIDC_ISSUER", defaultIssuer),
		ClientID: getEnv("ICB_CLIENT_ID", defaultClientID()),
		Audience: getEnv("ICB_OIDC_AUDIENCE", defaultAudience),
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
