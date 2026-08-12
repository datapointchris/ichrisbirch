package cli

import (
	"os"
	"testing"
)

// TestMain clears the machine-wide registry path for the whole package.
//
// Tests here build a temp XDG tree and assume the registry is whatever they put
// in it — usually nothing. $REPOS_JSON is set on any machine that maintains a
// registry and is read before XDG_DATA_HOME, so without this the suite reads the
// developer's real registry: TestWithoutARegistryNoProjectNameIsBanned found 80
// real repo names where it expected none, and failed by banning a name the test
// had never registered.
//
// Done here rather than per-test so a new test cannot reintroduce the leak by
// forgetting. A test that wants a declared path sets it itself with t.Setenv.
func TestMain(m *testing.M) {
	if err := os.Unsetenv("REPOS_JSON"); err != nil {
		panic(err)
	}
	os.Exit(m.Run())
}
