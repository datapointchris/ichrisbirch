package cli

import (
	"bytes"
	"errors"
	"testing"
)

func TestExitCodeFor(t *testing.T) {
	cases := []struct {
		name string
		err  error
		want int
	}{
		{"nil is success", nil, 0},
		{"usage error is 2", usageError{errors.New("bad flag")}, 2},
		{"exitCode carries its own value", exitCode(1), 1},
		{"exitCode two", exitCode(2), 2},
		{"generic runtime error is 1", errors.New("boom"), 1},
		{"wrapped usage error is 2", errWrap(usageError{errors.New("x")}), 2},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := exitCodeFor(c.err); got != c.want {
				t.Errorf("exitCodeFor(%v) = %d, want %d", c.err, got, c.want)
			}
		})
	}
}

// errWrap wraps err so errors.As still unwraps to the underlying type.
func errWrap(err error) error { return wrapped{err} }

type wrapped struct{ err error }

func (w wrapped) Error() string { return w.err.Error() }
func (w wrapped) Unwrap() error { return w.err }

// runTree executes the command tree with args, discarding output, and returns
// the classified exit code — the same path Execute() takes, minus os.Args.
func runTree(t *testing.T, args ...string) int {
	t.Helper()
	root := NewRootCommand()
	root.SetOut(&bytes.Buffer{})
	root.SetErr(&bytes.Buffer{})
	root.SetArgs(args)
	return exitCodeFor(root.Execute())
}

func TestCommandTree_ExitCodes(t *testing.T) {
	cases := []struct {
		name string
		args []string
		want int
	}{
		{"bare root shows help (success)", nil, 0},
		{"bare auth shows help (success)", []string{"auth"}, 0},
		{"unknown top-level command is usage error", []string{"nope"}, 2},
		{"unknown auth subcommand is usage error", []string{"auth", "nope"}, 2},
		{"unknown flag is usage error", []string{"--nonsense"}, 2},
		{"auth login rejects positional args", []string{"auth", "login", "extra"}, 2},
		{"auth status rejects positional args", []string{"auth", "status", "extra"}, 2},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := runTree(t, c.args...); got != c.want {
				t.Errorf("args %v exit = %d, want %d", c.args, got, c.want)
			}
		})
	}
}

func TestRootCommand_WiresAuthGroup(t *testing.T) {
	root := NewRootCommand()
	cmd, _, err := root.Find([]string{"auth"})
	if err != nil || cmd.Name() != "auth" {
		t.Errorf("expected %q command wired into root, got %v (err %v)", "auth", cmd, err)
	}
}
