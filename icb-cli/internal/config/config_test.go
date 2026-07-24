package config

import (
	"strings"
	"testing"
)

func TestLoad_EnvOverrides(t *testing.T) {
	t.Setenv("ICB_OIDC_ISSUER", "https://idp.example")
	t.Setenv("ICB_CLIENT_ID", "icb-cli-ci")
	t.Setenv("ICB_OIDC_AUDIENCE", "https://aud.example")
	t.Setenv("ICB_API_BASE", "https://api.example")

	cfg := Load()

	if cfg.Issuer != "https://idp.example" {
		t.Errorf("Issuer = %q", cfg.Issuer)
	}
	if cfg.ClientID != "icb-cli-ci" {
		t.Errorf("ClientID = %q", cfg.ClientID)
	}
	if cfg.Audience != "https://aud.example" {
		t.Errorf("Audience = %q", cfg.Audience)
	}
	if cfg.APIBase != "https://api.example" {
		t.Errorf("APIBase = %q", cfg.APIBase)
	}
}

// An env var set to the empty string must fall through to the default, not blank
// the field — getEnv treats "" as unset.
func TestLoad_EmptyEnvFallsThroughToDefault(t *testing.T) {
	t.Setenv("ICB_OIDC_ISSUER", "")
	t.Setenv("ICB_OIDC_AUDIENCE", "")
	t.Setenv("ICB_API_BASE", "")

	cfg := Load()

	if cfg.Issuer != defaultIssuer {
		t.Errorf("Issuer = %q, want default %q", cfg.Issuer, defaultIssuer)
	}
	if cfg.Audience != defaultAudience {
		t.Errorf("Audience = %q, want default %q", cfg.Audience, defaultAudience)
	}
	if cfg.APIBase != defaultAPIBase {
		t.Errorf("APIBase = %q, want default %q", cfg.APIBase, defaultAPIBase)
	}
}

// Without ICB_CLIENT_ID, the client id is derived from the short hostname and
// always carries the icb-cli- prefix (the per-machine × app naming).
func TestLoad_DefaultClientIDIsPerMachine(t *testing.T) {
	t.Setenv("ICB_CLIENT_ID", "")

	cfg := Load()

	if !strings.HasPrefix(cfg.ClientID, "icb-cli") {
		t.Errorf("ClientID = %q, want an icb-cli* value", cfg.ClientID)
	}
	if strings.ContainsAny(cfg.ClientID, ". ") {
		t.Errorf("ClientID = %q should be lowercased short hostname without domain/space", cfg.ClientID)
	}
	if cfg.ClientID != strings.ToLower(cfg.ClientID) {
		t.Errorf("ClientID = %q should be lowercase", cfg.ClientID)
	}
}
