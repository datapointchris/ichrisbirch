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
		{"bare projects shows help (success)", []string{"projects"}, 0},
		{"unknown top-level command is usage error", []string{"nope"}, 2},
		{"unknown auth subcommand is usage error", []string{"auth", "nope"}, 2},
		{"unknown projects subcommand is usage error", []string{"projects", "nope"}, 2},
		{"unknown flag is usage error", []string{"--nonsense"}, 2},
		{"auth login rejects positional args", []string{"auth", "login", "extra"}, 2},
		{"auth status rejects positional args", []string{"auth", "status", "extra"}, 2},
		{"projects view without an id is usage error", []string{"projects", "view"}, 2},
		{"projects create without --name is usage error", []string{"projects", "create"}, 2},
		{"projects edit with no fields is usage error", []string{"projects", "edit", "018f"}, 2},
		{"projects delete without an id is usage error", []string{"projects", "delete"}, 2},
		{"projects items without an id is usage error", []string{"projects", "items"}, 2},
		{"bare items shows help (success)", []string{"items"}, 0},
		{"unknown items subcommand is usage error", []string{"items", "nope"}, 2},
		{"items view without an id is usage error", []string{"items", "view"}, 2},
		{"items search without a query is usage error", []string{"items", "search"}, 2},
		{"items create without --title is usage error", []string{"items", "create", "--project", "p1"}, 2},
		{"items create without --project is usage error", []string{"items", "create", "--title", "x"}, 2},
		{"items edit with no fields is usage error", []string{"items", "edit", "018f"}, 2},
		{"items complete without an id is usage error", []string{"items", "complete"}, 2},
		{"items reorder without --project is usage error", []string{"items", "reorder", "018f", "--position", "1"}, 2},
		{"items add-project without --project is usage error", []string{"items", "add-project", "018f"}, 2},
		{"items add-dependency without --depends-on is usage error", []string{"items", "add-dependency", "018f"}, 2},
		{"items add-task without --title is usage error", []string{"items", "add-task", "018f"}, 2},
		{"items complete-task needs two ids", []string{"items", "complete-task", "018f"}, 2},
		{"items edit-task with no fields is usage error", []string{"items", "edit-task", "018f", "018g"}, 2},
		{"items remove-task needs two ids", []string{"items", "remove-task", "018f"}, 2},
		{"bare tasks shows help (success)", []string{"tasks"}, 0},
		{"unknown tasks subcommand is usage error", []string{"tasks", "nope"}, 2},
		{"tasks view without an id is usage error", []string{"tasks", "view"}, 2},
		{"tasks view with non-int id is usage error", []string{"tasks", "view", "abc"}, 2},
		{"tasks create without --name is usage error", []string{"tasks", "create", "--category", "c"}, 2},
		{"tasks create without --category is usage error", []string{"tasks", "create", "--name", "n"}, 2},
		{"tasks edit with no fields is usage error", []string{"tasks", "edit", "1"}, 2},
		{"tasks shift needs two args", []string{"tasks", "shift", "1"}, 2},
		{"tasks shift with non-int positions is usage error", []string{"tasks", "shift", "1", "x"}, 2},
		{"tasks complete without an id is usage error", []string{"tasks", "complete"}, 2},
		{"bare countdowns shows help (success)", []string{"countdowns"}, 0},
		{"countdowns view without an id is usage error", []string{"countdowns", "view"}, 2},
		{"countdowns create without --name is usage error", []string{"countdowns", "create", "--due", "2027-01-01"}, 2},
		{"countdowns create with bad --due is usage error", []string{"countdowns", "create", "--name", "x", "--due", "nope"}, 2},
		{"countdowns edit with no fields is usage error", []string{"countdowns", "edit", "1"}, 2},
		{"bare events shows help (success)", []string{"events"}, 0},
		{"events view without an id is usage error", []string{"events", "view"}, 2},
		{"events create without --venue is usage error", []string{"events", "create", "--name", "x", "--date", "2026-09-01"}, 2},
		{"events edit with no fields is usage error", []string{"events", "edit", "1"}, 2},
		{"events attend without an id is usage error", []string{"events", "attend"}, 2},
		{"bare habits shows help (success)", []string{"habits"}, 0},
		{"habits view without an id is usage error", []string{"habits", "view"}, 2},
		{"habits create without --name is usage error", []string{"habits", "create", "--category", "1"}, 2},
		{"habits create without --category is usage error", []string{"habits", "create", "--name", "x"}, 2},
		{"habits edit with no fields is usage error", []string{"habits", "edit", "1"}, 2},
		{"habits complete without an id is usage error", []string{"habits", "complete"}, 2},
		{"bare books shows help (success)", []string{"books"}, 0},
		{"books view without an id is usage error", []string{"books", "view"}, 2},
		{"books create without --title is usage error", []string{"books", "create", "--author", "a", "--tag", "t"}, 2},
		{"books create without a tag is usage error", []string{"books", "create", "--title", "t", "--author", "a"}, 2},
		{"books edit with no fields is usage error", []string{"books", "edit", "1"}, 2},
		{"books isbn without an isbn is usage error", []string{"books", "isbn"}, 2},
		{"bare articles shows help (success)", []string{"articles"}, 0},
		{"unknown articles subcommand is usage error", []string{"articles", "nope"}, 2},
		{"articles view without an id is usage error", []string{"articles", "view"}, 2},
		{"articles view with non-int id is usage error", []string{"articles", "view", "abc"}, 2},
		{"articles current rejects positional args", []string{"articles", "current", "extra"}, 2},
		{"articles search without a query is usage error", []string{"articles", "search"}, 2},
		{"articles create without --url is usage error", []string{"articles", "create", "--notes", "x"}, 2},
		{"articles edit with no fields is usage error", []string{"articles", "edit", "1"}, 2},
		{"articles read without an id is usage error", []string{"articles", "read"}, 2},
		{"articles delete without an id is usage error", []string{"articles", "delete"}, 2},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := runTree(t, c.args...); got != c.want {
				t.Errorf("args %v exit = %d, want %d", c.args, got, c.want)
			}
		})
	}
}

func TestRootCommand_WiresResourceGroups(t *testing.T) {
	root := NewRootCommand()
	for _, name := range []string{"auth", "projects", "items", "tasks", "countdowns", "events", "habits", "books", "articles"} {
		cmd, _, err := root.Find([]string{name})
		if err != nil || cmd.Name() != name {
			t.Errorf("expected %q command wired into root, got %v (err %v)", name, cmd, err)
		}
	}
}
