package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

// TestMain points XDG_CONFIG_HOME at an empty directory, so no test reads the
// developer's real config.toml and talks to their deployment.
//
// Done here rather than per-test so a new test cannot reintroduce the leak by
// forgetting. A test that wants a config writes its own with configure.
func TestMain(m *testing.M) {
	empty, err := os.MkdirTemp("", "icb-cli-config")
	if err != nil {
		panic(err)
	}
	if err := os.Setenv("XDG_CONFIG_HOME", empty); err != nil {
		panic(err)
	}
	code := m.Run()
	if err := os.RemoveAll(empty); err != nil {
		panic(err)
	}
	os.Exit(code)
}

// configure writes the config file every command reads its deployment from, in
// a config directory of the test's own.
func configure(t *testing.T, api, issuer, clientID string) {
	t.Helper()
	root := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", root)
	dir := filepath.Join(root, "icb")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	content := fmt.Sprintf("api = %q\nissuer = %q\nclient_id = %q\n", api, issuer, clientID)
	if err := os.WriteFile(filepath.Join(dir, "config.toml"), []byte(content), 0o600); err != nil {
		t.Fatal(err)
	}
}
