package cli

import (
	"strings"
	"testing"

	"github.com/spf13/cobra"
)

// findCommand walks the tree to the leaf named by path.
func findCommand(t *testing.T, path ...string) *cobra.Command {
	t.Helper()
	cmd := NewRootCommand()
	for _, name := range path {
		var next *cobra.Command
		for _, child := range cmd.Commands() {
			if child.Name() == name {
				next = child
				break
			}
		}
		if next == nil {
			t.Fatalf("no command %q under %q", name, cmd.CommandPath())
		}
		cmd = next
	}
	return cmd
}

// Every command whose verb is `list` reads a collection that grows outside the
// binary, so `cli-design.md` § "`--follow`/`-f` defaults to false; `--limit`/`-n`
// goes on every list" reaches all of them. Listing them here is what stops the
// next one being added without the flag.
func TestEveryListCommandTakesLimit(t *testing.T) {
	lists := [][]string{
		{"articles", "list"},
		{"autotasks", "list"},
		{"books", "list"},
		{"cooking-techniques", "list"},
		{"countdowns", "list"},
		{"events", "list"},
		{"habits", "list"},
		{"patterns", "list"},
		{"projects", "list"},
		{"projects", "items", "list"},
		{"recipes", "list"},
		{"tasks", "list"},
	}
	for _, path := range lists {
		t.Run(strings.Join(path, " "), func(t *testing.T) {
			flag := findCommand(t, path...).Flags().Lookup("limit")
			if flag == nil {
				t.Fatalf("%s has no --limit", strings.Join(path, " "))
			}
			if flag.Shorthand != "n" {
				t.Errorf("--limit shorthand = %q, want n", flag.Shorthand)
			}
		})
	}
}

// The two commands that cap client-side keep their own non-zero defaults, and
// still answer to the same spelling.
func TestClientSideCapsCarryTheSameFlag(t *testing.T) {
	for _, path := range [][]string{{"overview"}, {"projects", "items", "next"}} {
		t.Run(strings.Join(path, " "), func(t *testing.T) {
			flag := findCommand(t, path...).Flags().Lookup("limit")
			if flag == nil {
				t.Fatalf("%s has no --limit", strings.Join(path, " "))
			}
			if flag.Shorthand != "n" {
				t.Errorf("--limit shorthand = %q, want n", flag.Shorthand)
			}
		})
	}
}

// An unset flag is nil so the client omits the parameter; an explicit zero is a
// pointer to zero, which applyLimit then declines to send. Both mean every row,
// and they have to stay distinguishable here because only the first leaves the
// server free to apply its own default.
func TestLimitFlag_DistinguishesUnsetFromExplicitZero(t *testing.T) {
	cmd := findCommand(t, "tasks", "list")
	if got := limitFlag(cmd); got != nil {
		t.Errorf("limitFlag on an untouched command = %v, want nil", *got)
	}

	cmd = findCommand(t, "tasks", "list")
	if err := cmd.Flags().Set("limit", "0"); err != nil {
		t.Fatalf("set limit: %v", err)
	}
	got := limitFlag(cmd)
	if got == nil {
		t.Fatal("limitFlag after --limit 0 = nil, want a pointer to 0")
	}
	if *got != 0 {
		t.Errorf("limitFlag after --limit 0 = %d, want 0", *got)
	}
}

func TestLimitFlag_CarriesAnExplicitCap(t *testing.T) {
	cmd := findCommand(t, "books", "list")
	if err := cmd.Flags().Set("limit", "7"); err != nil {
		t.Fatalf("set limit: %v", err)
	}
	got := limitFlag(cmd)
	if got == nil || *got != 7 {
		t.Fatalf("limitFlag after --limit 7 = %v, want 7", got)
	}
}
