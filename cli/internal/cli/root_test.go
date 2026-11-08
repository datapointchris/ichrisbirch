package cli

import (
	"errors"
	"io"
	"os"
	"slices"
	"strings"
	"testing"

	"github.com/datapointchris/goselfupdate/autoupdate"
)

func TestExitCodeFor(t *testing.T) {
	cases := []struct {
		name string
		err  error
		want int
	}{
		{"exitCode carries its own value", exitCode(1), 1},
		{"generic runtime error is 1", errors.New("boom"), 1},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := exitCodeFor(c.err); got != c.want {
				t.Errorf("exitCodeFor(%v) = %d, want %d", c.err, got, c.want)
			}
		})
	}
}

// runLine drives the real tree through run, the path the shipped binary takes,
// with the version check suppressed. goclikit.Execute resolves the command
// from os.Args, so the line goes there rather than through SetArgs.
func runLine(t *testing.T, args ...string) error {
	t.Helper()
	original := os.Args
	os.Args = append([]string{"icb"}, args...)
	t.Cleanup(func() { os.Args = original })

	root := NewRootCommand()
	root.SetOut(io.Discard)
	root.SetErr(io.Discard)
	return run(root, autoupdate.Config{Suppress: true})
}

// A word one slip from a subcommand, or one its SuggestFor lists, is answered
// with the subcommand, at the root and inside a group alike.
func TestAnUnknownSubcommandNamesTheNearOnes(t *testing.T) {
	for _, c := range []struct {
		args  []string
		meant string
	}{
		{[]string{"tasjs"}, "tasks"},
		{[]string{"tasks", "lisy"}, "list"},
	} {
		err := runLine(t, c.args...)
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
		{"tasks", "categories", "bogus", "--json"},
	} {
		err := runLine(t, args...)
		if err == nil || !strings.Contains(err.Error(), `unknown command "bogus"`) {
			t.Errorf("%v answered %v, want it to refuse \"bogus\"", args, err)
		}
		if got := exitCodeFor(err); got != 2 {
			t.Errorf("%v exit = %d, want 2", args, got)
		}
	}
}

// cobra answers --help before it parses anything else, so a mistyped word
// asking for help would print the group's screen and exit 0 as though the word
// had been a subcommand.
func TestAWordTypedWithHelpIsRefusedAtEveryGroup(t *testing.T) {
	for _, args := range [][]string{
		{"tasks", "bogus", "--help"},
		{"tasks", "categories", "bogus", "-h"},
	} {
		err := runLine(t, args...)
		if err == nil || !strings.Contains(err.Error(), `unknown command "bogus"`) {
			t.Errorf("%v answered %v, want it to refuse \"bogus\"", args, err)
		}
		if got := exitCodeFor(err); got != 2 {
			t.Errorf("%v exit = %d, want 2", args, got)
		}
	}
}

// runTree drives the real tree through run, as runLine does, and returns the
// exit code Execute would.
func runTree(t *testing.T, args ...string) int {
	t.Helper()
	return exitCodeFor(runLine(t, args...))
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
		{"auth login rejects a second positional arg", []string{"auth", "login", "https://a.example", "extra"}, 2},
		{"bare tasks shows help (success)", []string{"tasks"}, 0},
		{"unknown tasks subcommand is usage error", []string{"tasks", "nope"}, 2},
		{"tasks show with non-int id is usage error", []string{"tasks", "show", "abc"}, 2},
		{"tasks create without --name is usage error", []string{"tasks", "create", "--category", "c"}, 2},
		{"tasks create without --category is usage error", []string{"tasks", "create", "--name", "n"}, 2},
		{"tasks edit with no fields is usage error", []string{"tasks", "edit", "1"}, 2},
		{"tasks reopen with non-int id is usage error", []string{"tasks", "reopen", "x"}, 2},
		{"tasks snooze with non-int id is usage error", []string{"tasks", "snooze", "x"}, 2},
		{"tasks unpin with non-int id is usage error", []string{"tasks", "unpin", "x"}, 2},
		{"tasks create with a zero window is usage error", []string{"tasks", "create", "--name", "n", "--category", "Chore", "--window-days", "0"}, 2},
		{"tasks edit with a zero window is usage error", []string{"tasks", "edit", "1", "--window-days", "0"}, 2},
		{"tasks list with an unknown status is usage error", []string{"tasks", "list", "--status", "closed"}, 2},
		{"bare tasks categories shows help (success)", []string{"tasks", "categories"}, 0},
		{"tasks categories edit without --window-days is usage error", []string{"tasks", "categories", "edit", "Home"}, 2},
		{"tasks categories edit with an unknown category is usage error", []string{"tasks", "categories", "edit", "Gardening", "--window-days", "3"}, 2},
		{"tasks categories edit with a zero window is usage error", []string{"tasks", "categories", "edit", "Home", "--window-days", "0"}, 2},
		{"bare countdowns shows help (success)", []string{"countdowns"}, 0},
		{"countdowns create without --name is usage error", []string{"countdowns", "create", "--due", "2027-01-01"}, 2},
		{"countdowns create with bad --due is usage error", []string{"countdowns", "create", "--name", "x", "--due", "nope"}, 2},
		{"countdowns edit with no fields is usage error", []string{"countdowns", "edit", "1"}, 2},
		{"bare events shows help (success)", []string{"events"}, 0},
		{"events create without --venue is usage error", []string{"events", "create", "--name", "x", "--date", "2026-09-01"}, 2},
		{"events edit with no fields is usage error", []string{"events", "edit", "1"}, 2},
		{"bare habits shows help (success)", []string{"habits"}, 0},
		{"habits create without --name is usage error", []string{"habits", "create", "--category", "1"}, 2},
		{"habits create without --category is usage error", []string{"habits", "create", "--name", "x"}, 2},
		{"habits edit with no fields is usage error", []string{"habits", "edit", "1"}, 2},
		{"bare books shows help (success)", []string{"books"}, 0},
		{"books create without --title is usage error", []string{"books", "create", "--author", "a", "--tag", "t"}, 2},
		{"books create without a tag is usage error", []string{"books", "create", "--title", "t", "--author", "a"}, 2},
		{"books edit with no fields is usage error", []string{"books", "edit", "1"}, 2},
		{"bare articles shows help (success)", []string{"articles"}, 0},
		{"unknown articles subcommand is usage error", []string{"articles", "nope"}, 2},
		{"articles show with non-int id is usage error", []string{"articles", "show", "abc"}, 2},
		{"articles create without --url is usage error", []string{"articles", "create", "--notes", "x"}, 2},
		{"articles edit with no fields is usage error", []string{"articles", "edit", "1"}, 2},
		{"recipes search with neither a query nor --ingredients is usage error", []string{"recipes", "search"}, 2},
		{"recipes search with a query and --ingredients is usage error", []string{"recipes", "search", "soup", "--ingredients", "leek"}, 2},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := runTree(t, c.args...); got != c.want {
				t.Errorf("args %v exit = %d, want %d", c.args, got, c.want)
			}
		})
	}
}
