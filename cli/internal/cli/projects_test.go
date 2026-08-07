package cli

import (
	"bytes"
	"strings"
	"testing"
	"time"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func intPtr(n int) *int { return &n }

func TestPrintProjectsTable_ShowsOpenAndDoneAlongsideTheTotal(t *testing.T) {
	projects := []api.Project{
		{ID: "018f-a", Name: "Personal OS", Kind: "build", Position: 0, ItemCount: intPtr(9), OpenCount: intPtr(3), CompletedCount: intPtr(4)},
		{ID: "018f-b", Name: "Finished thing", Kind: "chore", Position: 1, ItemCount: intPtr(5), OpenCount: intPtr(0), CompletedCount: intPtr(5)},
	}

	var out bytes.Buffer
	printProjectsTable(&out, projects, false)
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
	printProjectsTable(&out, []api.Project{{ID: "018f-a", Name: "Fresh", Kind: "build"}}, false)

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
	}, false)

	if !strings.Contains(out.String(), "ichrisbirch,icb,todoui") {
		t.Errorf("a project spanning repos must list all of them, got:\n%s", out.String())
	}
	if !strings.Contains(out.String(), "Not repo work") || !strings.Contains(out.String(), "—") {
		t.Errorf("a project with no repo work must render a dash, got:\n%s", out.String())
	}
}

func strPtr(s string) *string { return &s }

func TestPrintProjectsTable_OmitsTheStatusColumnByDefault(t *testing.T) {
	// The default list is active-only, so a column that reads "active" on every
	// row spends width to say nothing.
	var out bytes.Buffer
	printProjectsTable(&out, []api.Project{{ID: "018f-a", Name: "Live", Kind: "build", Status: "active"}}, false)

	if strings.Contains(out.String(), "STATUS") {
		t.Errorf("status column must be absent when every row is active, got:\n%s", out.String())
	}
}

func TestPrintProjectsTable_ShowsTheStatusColumnWhenAsked(t *testing.T) {
	var out bytes.Buffer
	printProjectsTable(&out, []api.Project{
		{ID: "018f-a", Name: "Live", Kind: "build", Status: "active"},
		{ID: "018f-b", Name: "Finished", Kind: "build", Status: "done"},
	}, true)

	lines := strings.Split(strings.TrimSpace(out.String()), "\n")
	if !strings.Contains(lines[0], "STATUS") {
		t.Fatalf("header %q is missing the STATUS column", lines[0])
	}
	if !strings.Contains(out.String(), "done") {
		t.Errorf("the terminal status must be rendered, got:\n%s", out.String())
	}
	if len(lines) != 3 {
		t.Errorf("got %d lines, want header + 2 rows:\n%s", len(lines), out.String())
	}
}

func TestPrintProjectDetail_NamesTheClosureAndItsReason(t *testing.T) {
	closed := time.Date(2026, 8, 1, 12, 0, 0, 0, time.UTC)
	var out bytes.Buffer
	printProjectDetail(&out, api.Project{
		ID: "018f-a", Name: "Rewrite in Rust", Kind: "build",
		Status: "dropped", StatusReason: strPtr("Go covers it"), ClosedAt: &closed,
		ItemCount: intPtr(3), OpenCount: intPtr(1), CompletedCount: intPtr(2),
	}, nil)

	for _, want := range []string{"dropped", "2026-08-01", "Go covers it"} {
		if !strings.Contains(out.String(), want) {
			t.Errorf("detail is missing %q, got:\n%s", want, out.String())
		}
	}
}

func TestPrintProjectDetail_OmitsTheReasonLineWhileActive(t *testing.T) {
	var out bytes.Buffer
	printProjectDetail(&out, api.Project{ID: "018f-a", Name: "Live", Kind: "build", Status: "active"}, nil)

	if strings.Contains(out.String(), "reason:") {
		t.Errorf("an active project has no closing reason to print, got:\n%s", out.String())
	}
	statusLine := lineContaining(t, out.String(), "status:")
	if strings.TrimSpace(statusLine) != "status:    active" {
		t.Errorf("status line = %q, want no closing date appended", statusLine)
	}
}

// lineContaining returns the single output line holding needle, failing the test
// when it is absent — an assertion on a whole dump reports "not found" without
// saying what was there instead.
func lineContaining(t *testing.T, output, needle string) string {
	t.Helper()
	for _, line := range strings.Split(output, "\n") {
		if strings.Contains(line, needle) {
			return line
		}
	}
	t.Fatalf("no line containing %q in:\n%s", needle, output)
	return ""
}
