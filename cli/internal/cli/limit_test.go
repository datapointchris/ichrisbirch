package cli

import (
	"strings"
	"testing"
)

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

// An unset flag is nil so the client omits the parameter and every row comes
// back; an explicit zero is a pointer to zero, which is sent and answers with
// nothing. The two are opposite answers, so the distinction is the whole
// contract rather than an implementation detail.
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

// The parser is the only thing standing between a negative and a slice
// expression, and `capItems` is where one would land: items[:-1] panics where a
// usage error was the answer. Every --limit is declared through addLimitFlag,
// so refusing here refuses everywhere.
func TestLimitFlag_RefusesANegative(t *testing.T) {
	for _, path := range [][]string{{"tasks", "list"}, {"overview"}, {"projects", "items", "next"}} {
		t.Run(strings.Join(path, " "), func(t *testing.T) {
			cmd := findCommand(t, path...)
			err := cmd.Flags().Set("limit", "-1")
			if err == nil {
				t.Fatal("--limit -1 was accepted, want a usage error")
			}
			if !strings.Contains(err.Error(), "zero or more") {
				t.Errorf("error = %q, want it to say what a row count may be", err)
			}
		})
	}
}

// Every --limit carries the same default the command had before it was routed
// through the shared factory: uncapped on the reads the API bounds, and a
// screenful on the two that cap what they print.
func TestLimitFlag_KeepsEachCommandsDefault(t *testing.T) {
	defaults := map[string][]string{
		"0":  {"tasks", "list"},
		"10": {"overview"},
	}
	for want, path := range defaults {
		t.Run(strings.Join(path, " "), func(t *testing.T) {
			flag := findCommand(t, path...).Flags().Lookup("limit")
			if flag.DefValue != want {
				t.Errorf("%s --limit default = %q, want %q", strings.Join(path, " "), flag.DefValue, want)
			}
		})
	}
}
