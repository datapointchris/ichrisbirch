package prompt

import (
	"io"
	"strings"
	"testing"
)

func TestSeedReader_HandsTheSeedOverBeforeTheStream(t *testing.T) {
	reader := &seedReader{src: strings.NewReader("typed")}
	reader.seed("Chorre")

	all, err := io.ReadAll(reader)
	if err != nil {
		t.Fatalf("ReadAll: %v", err)
	}
	if string(all) != "Chorretyped" {
		t.Errorf("read %q, want the seed first — that is what puts a rejected answer back on the line", all)
	}
}

func TestSeedReader_WithoutASeedIsJustTheStream(t *testing.T) {
	reader := &seedReader{src: strings.NewReader("typed")}

	all, err := io.ReadAll(reader)
	if err != nil {
		t.Fatalf("ReadAll: %v", err)
	}
	if string(all) != "typed" {
		t.Errorf("read %q, want the stream unchanged", all)
	}
}

// tab presses Tab on a line and reports what the cycler put there.
func tab(t *testing.T, c *cycler, line string) string {
	t.Helper()
	completed, pos, ok := c.complete(line, len(line), '\t')
	if !ok {
		t.Fatalf("Tab on %q completed nothing", line)
	}
	if pos != len(completed) {
		t.Errorf("cursor at %d, want the end of %q", pos, completed)
	}
	return completed
}

func TestCycler_TabWalksTheMatchesAndWraps(t *testing.T) {
	c := &cycler{choices: []string{"Chore", "Computer", "Dingo"}}

	if got := tab(t, c, "c"); got != "Chore" {
		t.Errorf("first Tab = %q, want Chore", got)
	}
	if got := tab(t, c, "Chore"); got != "Computer" {
		t.Errorf("second Tab = %q, want the next match", got)
	}
	if got := tab(t, c, "Computer"); got != "Chore" {
		t.Errorf("third Tab = %q, want the walk to wrap", got)
	}
}

func TestCycler_TabOnAnEmptyLineBrowsesEverything(t *testing.T) {
	c := &cycler{choices: []string{"Chore", "Computer"}}

	if got := tab(t, c, ""); got != "Chore" {
		t.Errorf("Tab on an empty line = %q, want the first choice", got)
	}
}

func TestCycler_TypingStartsANewCycle(t *testing.T) {
	c := &cycler{choices: []string{"Chore", "Computer", "Dingo"}}
	tab(t, c, "c")

	if _, _, ok := c.complete("d", 1, 'd'); ok {
		t.Fatal("a printable key was completed — only Tab completes")
	}
	if got := tab(t, c, "d"); got != "Dingo" {
		t.Errorf("Tab after typing = %q, want the cycle restarted from what is on the line", got)
	}
}

func TestCycler_NoMatchLeavesTheLineAlone(t *testing.T) {
	c := &cycler{choices: []string{"Chore"}}

	if _, _, ok := c.complete("zz", 2, '\t'); ok {
		t.Error("a prefix matching nothing was completed anyway")
	}
}

func TestCycler_WithoutChoicesNeverCompletes(t *testing.T) {
	c := &cycler{}

	if _, _, ok := c.complete("", 0, '\t'); ok {
		t.Error("a field with no choices completed on Tab")
	}
}

func TestCycler_KeepsWhatFollowsTheCursor(t *testing.T) {
	c := &cycler{choices: []string{"Chore"}}

	completed, pos, ok := c.complete("cX", 1, '\t')
	if !ok {
		t.Fatal("Tab completed nothing")
	}
	if completed != "ChoreX" {
		t.Errorf("line = %q, want the text after the cursor kept", completed)
	}
	if pos != len("Chore") {
		t.Errorf("cursor at %d, want it after the completion", pos)
	}
}
