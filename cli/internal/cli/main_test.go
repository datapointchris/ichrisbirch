package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

// TestMain clears every layer that can name a registry outside the temp tree
// these tests build.
//
// Tests here point XDG_DATA_HOME at a temp tree and assume the registry is
// whatever they put in it — usually nothing. $ICB_REPOS_REGISTRY and icb's own
// config both resolve ahead of that, so without this the suite reads the
// developer's real registry: TestWithoutARegistryNoProjectNameIsBanned found 80
// real repo names where it expected none, and failed by banning a name the test
// had never registered. The config file is neutralized by pointing
// XDG_CONFIG_HOME at an empty directory, since there is no variable that turns
// it off.
//
// Done here rather than per-test so a new test cannot reintroduce the leak by
// forgetting. A test that wants a declared path sets it itself with t.Setenv.
func TestMain(m *testing.M) {
	if err := os.Unsetenv("ICB_REPOS_REGISTRY"); err != nil {
		panic(err)
	}
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
