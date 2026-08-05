package cli

import (
	"testing"

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
