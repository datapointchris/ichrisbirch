package cli

import (
	"os"
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
