package cli

import (
	"bytes"
	"strings"
	"testing"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func intPtr(n int) *int { return &n }

func TestPrintProjectsTable_ShowsOpenAndDoneAlongsideTheTotal(t *testing.T) {
	projects := []api.Project{
		{ID: "018f-a", Name: "Personal OS", Kind: "build", Position: 0, ItemCount: intPtr(9), OpenCount: intPtr(3), CompletedCount: intPtr(4)},
		{ID: "018f-b", Name: "Finished thing", Kind: "chore", Position: 1, ItemCount: intPtr(5), OpenCount: intPtr(0), CompletedCount: intPtr(5)},
	}

	var out bytes.Buffer
	printProjectsTable(&out, projects)
	lines := strings.Split(strings.TrimSpace(out.String()), "\n")

	if len(lines) != 3 {
		t.Fatalf("got %d lines, want header + 2 rows:\n%s", len(lines), out.String())
	}
	for _, want := range []string{"OPEN", "DONE", "ITEMS"} {
		if !strings.Contains(lines[0], want) {
			t.Errorf("header %q is missing the %s column", lines[0], want)
		}
	}
	// The reason the columns exist: a project with nothing open must be
	// distinguishable from one with work left, which the total alone hides.
	if !strings.Contains(lines[1], "3") || !strings.Contains(lines[2], "0") {
		t.Errorf("rows do not carry the open counts:\n%s", out.String())
	}
}

func TestPrintProjectsTable_DashesCountsTheServerOmitted(t *testing.T) {
	var out bytes.Buffer
	printProjectsTable(&out, []api.Project{{ID: "018f-a", Name: "Fresh", Kind: "build"}})

	// Counted per column rather than over the whole row: a bare total silently
	// absorbs the next column added and stops testing anything.
	row := strings.Fields(strings.Split(out.String(), "\n")[1])
	for _, column := range []struct {
		index int
		name  string
	}{{3, "open"}, {4, "done"}, {5, "items"}} {
		if row[column.index] != "—" {
			t.Errorf("want a dash for the absent %s count, got %q in:\n%s", column.name, row[column.index], out.String())
		}
	}
}

func TestPrintProjectsTable_ShowsTheReposAProjectTouches(t *testing.T) {
	var out bytes.Buffer
	printProjectsTable(&out, []api.Project{
		{ID: "018f-a", Name: "Spans three", Kind: "build", Repos: []string{"ichrisbirch", "icb", "todoui"}},
		{ID: "018f-b", Name: "Not repo work", Kind: "life"},
	})

	if !strings.Contains(out.String(), "ichrisbirch,icb,todoui") {
		t.Errorf("a project spanning repos must list all of them, got:\n%s", out.String())
	}
	if !strings.Contains(out.String(), "Not repo work") || !strings.Contains(out.String(), "—") {
		t.Errorf("a project with no repo work must render a dash, got:\n%s", out.String())
	}
}
