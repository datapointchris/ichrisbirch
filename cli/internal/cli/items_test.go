package cli

import (
	"bytes"
	"strings"
	"testing"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func TestItemsOfKind_KeepsOnlyMatchingProjects(t *testing.T) {
	selling := api.Project{ID: "selling", Name: "Sell Unused Shite", Kind: "chore"}
	rollout := api.Project{ID: "rollout", Name: "Forge toolchain rollout", Kind: "build"}

	all := []api.ProjectItem{
		{ID: "glove-80", Projects: []api.Project{selling}},
		{ID: "exit-code", Projects: []api.Project{rollout}},
	}

	kept := itemsOfKind(all, "build")

	if len(kept) != 1 || kept[0].ID != "exit-code" {
		t.Errorf("itemsOfKind(build) = %s, want only exit-code", itemIDs(kept))
	}
}

func TestItemsOfKind_EmptyKindIsNoFilter(t *testing.T) {
	all := []api.ProjectItem{
		{ID: "a", Projects: []api.Project{{ID: "p", Kind: "chore"}}},
		{ID: "b", Projects: []api.Project{{ID: "q", Kind: "build"}}},
	}

	if kept := itemsOfKind(all, ""); len(kept) != 2 {
		t.Errorf("itemsOfKind(\"\") = %s, want every item — an unset flag filters nothing", itemIDs(kept))
	}
}

func TestItemsOfKind_MultiProjectItemKeptOnceWhenAnyProjectMatches(t *testing.T) {
	selling := api.Project{ID: "selling", Kind: "chore"}
	linux := api.Project{ID: "linux", Kind: "build"}

	all := []api.ProjectItem{{ID: "mac-mini", Projects: []api.Project{linux, selling}}}

	kept := itemsOfKind(all, "build")

	if len(kept) != 1 || kept[0].ID != "mac-mini" {
		t.Errorf("itemsOfKind(build) = %s, want mac-mini exactly once", itemIDs(kept))
	}
}

// The regression the kind column exists for: an errand filed as a project item
// was the oldest open item anywhere, so it was the answer to "what next" for a
// pursuit that meant making something.
func TestNextProjectItems_KindFilterKeepsTheErrandOutOfBuildWork(t *testing.T) {
	selling := api.Project{ID: "selling", Name: "Sell Unused Shite", Kind: "chore", CreatedAt: fixedNow.AddDate(0, 0, -120)}
	rollout := api.Project{ID: "rollout", Name: "Forge toolchain rollout", Kind: "build", CreatedAt: fixedNow.AddDate(0, 0, -30)}

	all := []api.ProjectItem{
		{ID: "glove-80", CreatedAt: fixedNow.AddDate(0, 0, -119), Projects: []api.Project{selling}},
		{ID: "exit-code", CreatedAt: fixedNow.AddDate(0, 0, -9), Projects: []api.Project{rollout}},
	}

	if unfiltered := nextProjectItems(all, nil); unfiltered[0].ID != "glove-80" {
		t.Fatalf("precondition: unfiltered next = %s, want the oldest item first", itemIDs(unfiltered))
	}

	next := nextProjectItems(itemsOfKind(all, "build"), nil)

	if len(next) != 1 || next[0].ID != "exit-code" {
		t.Errorf("next(build) = %s, want only exit-code", itemIDs(next))
	}
}

func TestItemsOfKind_UnknownKindReturnsNothing(t *testing.T) {
	all := []api.ProjectItem{{ID: "a", Projects: []api.Project{{ID: "p", Kind: "build"}}}}

	if kept := itemsOfKind(all, "errand"); len(kept) != 0 {
		t.Errorf("itemsOfKind(unknown) = %s, want nothing", itemIDs(kept))
	}
}

// The row has to carry the handle you can type. It printed the UUID, which is
// the key: 36 characters that resolve nothing a reader can retype.
func TestPrintItemsTable_ShowsTheNumberNotTheUUID(t *testing.T) {
	var out strings.Builder
	printItemsTable(&out, []api.ProjectItem{
		{ID: "019fdd05-1686-7571-8a27-9f73c1e9f20f", Number: 118, Title: "Give items a number"},
	})

	rendered := out.String()
	if !strings.Contains(rendered, "118") {
		t.Errorf("table = %q, want the item number in the ID column", rendered)
	}
	if strings.Contains(rendered, "019fdd05-1686-7571-8a27-9f73c1e9f20f") {
		t.Errorf("table = %q, want no UUID — it is the key, not the handle", rendered)
	}
}

func TestPrintItemDetail_ShowsTheNumberNotTheUUID(t *testing.T) {
	var out strings.Builder
	printItemDetail(&out, api.ProjectItemDetail{
		ID:     "019fdd05-1686-7571-8a27-9f73c1e9f20f",
		Number: 118,
		Title:  "Give items a number",
	}, nil, nil)

	rendered := out.String()
	if !strings.Contains(rendered, "id:      118") {
		t.Errorf("detail = %q, want the number on the id line", rendered)
	}
	if strings.Contains(rendered, "019fdd05-1686-7571-8a27-9f73c1e9f20f") {
		t.Errorf("detail = %q, want no UUID — --json is where a caller gets the key", rendered)
	}
}

// --archived was a second spelling of --status archived, which cli-design.md
// § "A lifecycle is one --status enum" rules out as a question-shaped alias
// beside the enum. Its removal is the point, so the flag's absence is pinned.
func TestItemsList_HasNoArchivedAliasBesideStatus(t *testing.T) {
	cmd := newItemsListCommand()
	if cmd.Flags().Lookup("archived") != nil {
		t.Error("--archived is back; --status archived and --status all already say it")
	}
	if cmd.Flags().Lookup("status") == nil {
		t.Fatal("--status is missing from the list command")
	}
}

// A scope selects which rows come back, not which states, so --project takes
// --status rather than refusing it.
func TestItemsList_ProjectAcceptsStatus(t *testing.T) {
	cmd := newItemsListCommand()
	if err := cmd.Flags().Parse([]string{"--project", "todoui", "--status", "completed"}); err != nil {
		t.Fatalf("--status alongside --project: %v", err)
	}
}

func TestHintHiddenItems_NamesTheCommandThatRan(t *testing.T) {
	cmd := newItemsListCommand()
	root := &cobra.Command{Use: "icb"}
	root.AddCommand(cmd)
	if err := cmd.Flags().Parse([]string{"--project", "todoui"}); err != nil {
		t.Fatalf("parse: %v", err)
	}
	var stderr bytes.Buffer
	cmd.SetErr(&stderr)

	hintHiddenItems(cmd, false, "")

	got := stderr.String()
	// The scoped read quotes itself back; dropping --project would hand over a
	// command that answers a different question from the one just asked.
	if !strings.Contains(got, "icb list --project todoui --status all") {
		t.Errorf("hint = %q, want it to carry --project todoui and --status all", got)
	}
}

func TestHintHiddenItems_SilentWhenTheCallerChoseAStatus(t *testing.T) {
	cmd := newItemsListCommand()
	if err := cmd.Flags().Parse([]string{"--status", "all"}); err != nil {
		t.Fatalf("parse: %v", err)
	}
	var stderr bytes.Buffer
	cmd.SetErr(&stderr)

	hintHiddenItems(cmd, false, "all")

	if stderr.String() != "" {
		t.Errorf("hint = %q, want silence when the status was asked for", stderr.String())
	}
}

func TestProjectsShow_TakesStatusNotArchived(t *testing.T) {
	cmd := newProjectsShowCommand()
	if cmd.Flags().Lookup("archived") != nil {
		t.Error("--archived is back on projects show")
	}
	if cmd.Flags().Lookup("status") == nil {
		t.Error("--status is missing from projects show")
	}
}

func TestShellQuote_LeavesAPlainWordAloneAndQuotesTheRest(t *testing.T) {
	for input, want := range map[string]string{
		"todoui":                  "todoui",
		"Forge toolchain rollout": "'Forge toolchain rollout'",
		"it's":                    `'it'\''s'`,
		"":                        "''",
	} {
		if got := shellQuote(input); got != want {
			t.Errorf("shellQuote(%q) = %s, want %s", input, got, want)
		}
	}
}

func TestHintHiddenItems_QuotesAProjectNameWithSpaces(t *testing.T) {
	cmd := newItemsListCommand()
	root := &cobra.Command{Use: "icb"}
	root.AddCommand(cmd)
	if err := cmd.Flags().Parse([]string{"--project", "Forge toolchain rollout"}); err != nil {
		t.Fatalf("parse: %v", err)
	}
	var stderr bytes.Buffer
	cmd.SetErr(&stderr)

	hintHiddenItems(cmd, false, "")

	if !strings.Contains(stderr.String(), "--project 'Forge toolchain rollout' --status all") {
		t.Errorf("hint = %q, want the project name quoted so it pastes back as one argument", stderr.String())
	}
}
