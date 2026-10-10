package cli

import (
	"bytes"
	"errors"
	"slices"
	"strings"
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

// A word one slip from a subcommand, or one its SuggestFor lists, is answered
// with the subcommand, at the root and inside a group alike.
func TestAnUnknownSubcommandNamesTheNearOnes(t *testing.T) {
	for _, c := range []struct {
		args  []string
		meant string
	}{
		{[]string{"tasjs"}, "tasks"},
		{[]string{"tasks", "lisy"}, "list"},
		{[]string{"items", "show", "848"}, "issues"},
		{[]string{"show", "848", "--json"}, "issues"},
		{[]string{"search", "golang"}, "issues"},
		{[]string{"projects", "itms", "--json"}, "items"},
		{[]string{"projects", "items", "lisz", "--json"}, "list"},
	} {
		root := NewRootCommand()
		root.SetOut(&bytes.Buffer{})
		root.SetErr(&bytes.Buffer{})
		root.SetArgs(c.args)
		err := root.Execute()
		if err == nil || !slices.Contains(strings.Fields(err.Error()), c.meant) {
			t.Errorf("%v answered %v, want it to name %q", c.args, err, c.meant)
		}
	}
}

// A flag the leaf would have taken, typed after a word naming no subcommand,
// leaves the word as the mistake at every depth.
func TestAFlagAfterAnUnknownWordRefusesTheWord(t *testing.T) {
	for _, args := range [][]string{
		{"bogus", "search", "foo", "--json"},
		{"projects", "bogus", "--json"},
		{"projects", "items", "bogus", "5", "--json"},
		{"tasks", "categories", "bogus", "--json"},
	} {
		root := NewRootCommand()
		root.SetOut(&bytes.Buffer{})
		root.SetErr(&bytes.Buffer{})
		root.SetArgs(args)
		err := root.Execute()
		if err == nil || !strings.Contains(err.Error(), `unknown command "bogus"`) {
			t.Errorf("%v answered %v, want it to refuse \"bogus\"", args, err)
		}
		if got := exitCodeFor(err); got != 2 {
			t.Errorf("%v exit = %d, want 2", args, got)
		}
	}
}

// A positional on a leaf is refused as an argument, never as a command, and a
// leaf taking that value through a flag spells the line that passes it there.
func TestAPositionalOnALeafIsRefusedAsAnArgument(t *testing.T) {
	for _, c := range []struct {
		args []string
		want string
	}{
		{[]string{"overview", "extra"}, `icb overview takes no arguments, and was given "extra"`},
		{[]string{"projects", "items", "list", "ypl"}, "icb projects items list --project ypl"},
		{[]string{"projects", "items", "list", "Kitchen remodel"}, "icb projects items list --project 'Kitchen remodel'"},
	} {
		root := NewRootCommand()
		root.SetOut(&bytes.Buffer{})
		root.SetErr(&bytes.Buffer{})
		root.SetArgs(c.args)
		err := root.Execute()
		if err == nil || !strings.Contains(err.Error(), c.want) || strings.Contains(err.Error(), "unknown command") {
			t.Errorf("%v answered %v, want it to carry %q", c.args, err, c.want)
		}
		if got := exitCodeFor(err); got != 2 {
			t.Errorf("%v exit = %d, want 2", c.args, got)
		}
	}
}

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
		{"overview rejects positional args", []string{"overview", "extra"}, 2},
		{"auth login rejects positional args", []string{"auth", "login", "extra"}, 2},
		{"auth status rejects positional args", []string{"auth", "status", "extra"}, 2},
		{"projects show without an id is usage error", []string{"projects", "show"}, 2},
		{"projects create without --name is usage error", []string{"projects", "create"}, 2},
		{"projects edit with no fields is usage error", []string{"projects", "edit", "018f"}, 2},
		{"projects complete without an id is usage error", []string{"projects", "complete"}, 2},
		{"projects reopen without an id is usage error", []string{"projects", "reopen"}, 2},
		{"projects drop without an id is usage error", []string{"projects", "drop"}, 2},
		{"projects drop without --reason is usage error", []string{"projects", "drop", "018f"}, 2},
		{"projects delete without an id is usage error", []string{"projects", "delete"}, 2},
		{"bare projects items shows help (success)", []string{"projects", "items"}, 0},
		{"items is no longer a root command", []string{"items"}, 2},
		{"unknown projects items subcommand is usage error", []string{"projects", "items", "nope"}, 2},
		{"projects items list --archived without --project is usage error", []string{"projects", "items", "list", "--archived"}, 2},
		{"projects items show without an id is usage error", []string{"projects", "items", "show"}, 2},
		{"projects items search without a query is usage error", []string{"projects", "items", "search"}, 2},
		{"projects items create without --title is usage error", []string{"projects", "items", "create", "--project", "p1"}, 2},
		{"projects items create without --project is usage error", []string{"projects", "items", "create", "--title", "x"}, 2},
		{"projects items edit with no fields is usage error", []string{"projects", "items", "edit", "018f"}, 2},
		{"projects items complete without an id is usage error", []string{"projects", "items", "complete"}, 2},
		{"projects items reorder without --project is usage error", []string{"projects", "items", "reorder", "018f", "--position", "1"}, 2},
		{"projects items add-project without --project is usage error", []string{"projects", "items", "add-project", "018f"}, 2},
		{"projects items add-dependency without --depends-on is usage error", []string{"projects", "items", "add-dependency", "018f"}, 2},
		{"projects items add-task without --title is usage error", []string{"projects", "items", "add-task", "018f"}, 2},
		{"projects items complete-task needs two ids", []string{"projects", "items", "complete-task", "018f"}, 2},
		{"projects items edit-task with no fields is usage error", []string{"projects", "items", "edit-task", "018f", "018g"}, 2},
		{"projects items remove-task needs two ids", []string{"projects", "items", "remove-task", "018f"}, 2},
		{"bare tasks shows help (success)", []string{"tasks"}, 0},
		{"unknown tasks subcommand is usage error", []string{"tasks", "nope"}, 2},
		{"tasks show without an id is usage error", []string{"tasks", "show"}, 2},
		{"tasks show with non-int id is usage error", []string{"tasks", "show", "abc"}, 2},
		{"tasks create without --name is usage error", []string{"tasks", "create", "--category", "c"}, 2},
		{"tasks create without --category is usage error", []string{"tasks", "create", "--name", "n"}, 2},
		{"tasks edit with no fields is usage error", []string{"tasks", "edit", "1"}, 2},
		{"tasks reopen without an id is usage error", []string{"tasks", "reopen"}, 2},
		{"tasks reopen with non-int id is usage error", []string{"tasks", "reopen", "x"}, 2},
		{"tasks snooze without an id is usage error", []string{"tasks", "snooze"}, 2},
		{"tasks snooze with non-int id is usage error", []string{"tasks", "snooze", "x"}, 2},
		{"tasks pin without an id is usage error", []string{"tasks", "pin"}, 2},
		{"tasks unpin with non-int id is usage error", []string{"tasks", "unpin", "x"}, 2},
		{"tasks drop without an id is usage error", []string{"tasks", "drop"}, 2},
		{"tasks create with a zero window is usage error", []string{"tasks", "create", "--name", "n", "--category", "Chore", "--window-days", "0"}, 2},
		{"tasks edit with a zero window is usage error", []string{"tasks", "edit", "1", "--window-days", "0"}, 2},
		{"tasks list with an unknown status is usage error", []string{"tasks", "list", "--status", "closed"}, 2},
		{"bare tasks categories shows help (success)", []string{"tasks", "categories"}, 0},
		{"tasks categories edit without --window-days is usage error", []string{"tasks", "categories", "edit", "Home"}, 2},
		{"tasks categories edit with an unknown category is usage error", []string{"tasks", "categories", "edit", "Gardening", "--window-days", "3"}, 2},
		{"tasks categories edit with a zero window is usage error", []string{"tasks", "categories", "edit", "Home", "--window-days", "0"}, 2},
		{"tasks complete without an id is usage error", []string{"tasks", "complete"}, 2},
		{"bare countdowns shows help (success)", []string{"countdowns"}, 0},
		{"countdowns show without an id is usage error", []string{"countdowns", "show"}, 2},
		{"countdowns create without --name is usage error", []string{"countdowns", "create", "--due", "2027-01-01"}, 2},
		{"countdowns create with bad --due is usage error", []string{"countdowns", "create", "--name", "x", "--due", "nope"}, 2},
		{"countdowns edit with no fields is usage error", []string{"countdowns", "edit", "1"}, 2},
		{"bare events shows help (success)", []string{"events"}, 0},
		{"events show without an id is usage error", []string{"events", "show"}, 2},
		{"events create without --venue is usage error", []string{"events", "create", "--name", "x", "--date", "2026-09-01"}, 2},
		{"events edit with no fields is usage error", []string{"events", "edit", "1"}, 2},
		{"events attend without an id is usage error", []string{"events", "attend"}, 2},
		{"bare habits shows help (success)", []string{"habits"}, 0},
		{"habits show without an id is usage error", []string{"habits", "show"}, 2},
		{"habits create without --name is usage error", []string{"habits", "create", "--category", "1"}, 2},
		{"habits create without --category is usage error", []string{"habits", "create", "--name", "x"}, 2},
		{"habits edit with no fields is usage error", []string{"habits", "edit", "1"}, 2},
		{"habits complete without an id is usage error", []string{"habits", "complete"}, 2},
		{"bare books shows help (success)", []string{"books"}, 0},
		{"books show without an id is usage error", []string{"books", "show"}, 2},
		{"books create without --title is usage error", []string{"books", "create", "--author", "a", "--tag", "t"}, 2},
		{"books create without a tag is usage error", []string{"books", "create", "--title", "t", "--author", "a"}, 2},
		{"books edit with no fields is usage error", []string{"books", "edit", "1"}, 2},
		{"books isbn without an isbn is usage error", []string{"books", "isbn"}, 2},
		{"bare articles shows help (success)", []string{"articles"}, 0},
		{"unknown articles subcommand is usage error", []string{"articles", "nope"}, 2},
		{"articles show without an id is usage error", []string{"articles", "show"}, 2},
		{"articles show with non-int id is usage error", []string{"articles", "show", "abc"}, 2},
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
	for _, name := range []string{"auth", "projects", "tasks", "countdowns", "events", "habits", "books", "articles"} {
		cmd, _, err := root.Find([]string{name})
		if err != nil || cmd.Name() != name {
			t.Errorf("expected %q command wired into root, got %v (err %v)", name, cmd, err)
		}
	}
	cmd, _, err := root.Find([]string{"projects", "items"})
	if err != nil || cmd.Name() != "items" {
		t.Errorf("expected items wired under projects, got %v (err %v)", cmd, err)
	}
}

// The update command has to carry a tag prefix. Without one it asks GitHub for
// the repository-wide latest release, which is the application's, not this
// binary's — and that fails as "not a semantic version" rather than visibly.
func TestRootCommand_WiresUpdate(t *testing.T) {
	root := NewRootCommand()

	cmd, _, err := root.Find([]string{"update"})
	if err != nil || cmd.Name() != "update" {
		t.Fatalf("update not wired into root: %v (err %v)", cmd, err)
	}
	if cmd.Flags().Lookup("check") == nil {
		t.Error("update should carry --check for reporting without installing")
	}
}
