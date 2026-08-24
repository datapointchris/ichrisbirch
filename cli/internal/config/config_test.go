package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoad_EnvOverrides(t *testing.T) {
	t.Setenv("ICB_OIDC_ISSUER", "https://idp.example")
	t.Setenv("ICB_CLIENT_ID", "icb-cli-ci")
	t.Setenv("ICB_API_BASE", "https://api.example")

	cfg := Load()

	if cfg.Issuer != "https://idp.example" {
		t.Errorf("Issuer = %q", cfg.Issuer)
	}
	if cfg.ClientID != "icb-cli-ci" {
		t.Errorf("ClientID = %q", cfg.ClientID)
	}
	if cfg.APIBase != "https://api.example" {
		t.Errorf("APIBase = %q", cfg.APIBase)
	}
}

// Login is the seam between icb's settings and goclilogin's, so what it carries
// across is worth pinning. The keyring service is a deployed identifier that
// several released versions already wrote under, and LockDir has to stay on
// icb's own state directory rather than take goclilogin's default — two
// versions naming different lock files would not exclude each other during an
// upgrade.
func TestLoginCarriesTheDeployedIdentifiers(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")
	t.Setenv("ICB_OIDC_ISSUER", "https://auth.example.com")
	t.Setenv("ICB_CLIENT_ID", "icb-cli-somehost")

	login := Load().Login()
	if login.Issuer != "https://auth.example.com" {
		t.Errorf("Issuer = %q", login.Issuer)
	}
	if login.ClientID != "icb-cli-somehost" {
		t.Errorf("ClientID = %q", login.ClientID)
	}
	if login.KeyringService != "icb-cli" {
		t.Errorf("KeyringService = %q, want icb-cli", login.KeyringService)
	}
	if login.LockDir != "/tmp/xdgstate/icb" {
		t.Errorf("LockDir = %q, want icb's own state directory", login.LockDir)
	}
}

// The client id spells the machine into it, so one machine's token is revocable
// without touching another's.
func TestDefaultClientIDIsPerMachine(t *testing.T) {
	t.Setenv("ICB_CLIENT_ID", "")
	got := Load().ClientID
	if !strings.HasPrefix(got, "icb-cli-") {
		t.Errorf("ClientID = %q, want an icb-cli-<host> spelling", got)
	}
}

// An env var set to the empty string must fall through to the default, not blank
// the field — getEnv treats "" as unset.
func TestLoad_EmptyEnvFallsThroughToDefault(t *testing.T) {
	t.Setenv("ICB_OIDC_ISSUER", "")
	t.Setenv("ICB_API_BASE", "")

	cfg := Load()

	if cfg.Issuer != defaultIssuer {
		t.Errorf("Issuer = %q, want default %q", cfg.Issuer, defaultIssuer)
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

// writeMachineConfig puts a config file where MachineConfigPath resolves to.
func writeMachineConfig(t *testing.T, body string) {
	t.Helper()
	root := t.TempDir()
	dir := filepath.Join(root, "icb")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		t.Fatalf("creating config dir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "config.yml"), []byte(body), 0o600); err != nil {
		t.Fatalf("writing config: %v", err)
	}
	t.Setenv("XDG_CONFIG_HOME", root)
}

func TestMachineConfigPathIsTheToolsOwnConfigDirectory(t *testing.T) {
	t.Setenv("XDG_CONFIG_HOME", "/tmp/xdgconfig")
	if got, want := MachineConfigPath(), "/tmp/xdgconfig/icb/config.yml"; got != want {
		t.Errorf("MachineConfigPath() = %q, want %q", got, want)
	}
}

func TestLoadMachineConfigReadsReposRegistry(t *testing.T) {
	writeMachineConfig(t, "repos_registry: ~/dev/repos.json\n")
	if got, want := LoadMachineConfig().ReposRegistry, "~/dev/repos.json"; got != want {
		t.Errorf("ReposRegistry = %q, want %q", got, want)
	}
}

// The config is optional, so its absence is the zero value rather than a failure.
// A machine keeping the registry where icb expects it holds no config file.
func TestLoadMachineConfigTreatsAnAbsentFileAsEmpty(t *testing.T) {
	t.Setenv("XDG_CONFIG_HOME", t.TempDir())
	if got := LoadMachineConfig().ReposRegistry; got != "" {
		t.Errorf("ReposRegistry = %q, want empty for an absent config", got)
	}
}

// A malformed config falls through for the same reason an absent one does:
// erroring would break the machine that needs no config at all.
func TestLoadMachineConfigTreatsMalformedYAMLAsEmpty(t *testing.T) {
	writeMachineConfig(t, "repos_registry: [not, a, string\n")
	if got := LoadMachineConfig().ReposRegistry; got != "" {
		t.Errorf("ReposRegistry = %q, want empty for a malformed config", got)
	}
}

func TestExpandTildeResolvesALeadingHome(t *testing.T) {
	home, err := os.UserHomeDir()
	if err != nil {
		t.Skipf("no home directory: %v", err)
	}
	if got, want := ExpandTilde("~/dev/repos.json"), filepath.Join(home, "dev", "repos.json"); got != want {
		t.Errorf("ExpandTilde = %q, want %q", got, want)
	}
	for _, path := range []string{"/absolute/repos.json", "relative/repos.json", ""} {
		if got := ExpandTilde(path); got != path {
			t.Errorf("ExpandTilde(%q) = %q, want it untouched", path, got)
		}
	}
}

func TestStatePathIsTheToolsOwnStateDirectory(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")
	if got, want := StatePath(), "/tmp/xdgstate/icb"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
	if got, want := StatePath("icb-cli-archlinux.refresh.lock"), "/tmp/xdgstate/icb/icb-cli-archlinux.refresh.lock"; got != want {
		t.Errorf("StatePath(name) = %q, want %q", got, want)
	}
}

func TestStatePathFallsBackToLocalState(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "")
	t.Setenv("HOME", "/home/tester")
	if got, want := StatePath(), "/home/tester/.local/state/icb"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
}
