package cli

import (
	"strings"
	"testing"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/graph"
)

func day() api.Project { return api.Project{ID: "day", Name: "day — the programmable day"} }
func home() api.Project {
	return api.Project{ID: "ha", Name: "Home Assistant and the first Zigbee scenes"}
}

func treeItems() []api.ProjectItem {
	return []api.ProjectItem{
		{ID: "a", Number: 181, Title: "Home Assistant as an effector", Projects: []api.Project{home()}, DependencyIDs: []string{"b"}},
		{ID: "b", Number: 179, Title: "day serve — the durable runner", Projects: []api.Project{day()}, DependencyIDs: []string{"c"}},
		{ID: "c", Number: 178, Title: "Day template schema", Completed: true, Projects: []api.Project{day()}},
	}
}

func indexed(items []api.ProjectItem) (*graph.Graph, map[string]api.ProjectItem) {
	byID := make(map[string]api.ProjectItem, len(items))
	nodes := make([]graph.Node, 0, len(items))
	for _, it := range items {
		byID[it.ID] = it
		nodes = append(nodes, graph.Node{ID: it.ID, Order: it.Number, Deps: it.DependencyIDs})
	}
	return graph.Build(nodes), byID
}

// allTrees is the no-argument selection: one drawing per component, rooted at
// whichever end the direction puts on top.
func allTrees(g *graph.Graph, invert bool) []drawTree {
	var trees []drawTree
	for _, members := range g.Components() {
		trees = append(trees, drawTree{roots: g.Roots(members, invert), members: members})
	}
	return trees
}

func TestTreeLine_CarriesTheCornerTheMarkAndTheNumber(t *testing.T) {
	_, byID := indexed(treeItems())

	line := treeLine(graph.Row{ID: "b", Depth: 1, Last: []bool{true}, Parent: "a"}, byID)

	if !strings.HasPrefix(line, "└── ") {
		t.Errorf("line = %q, want a last-child corner", line)
	}
	if !strings.Contains(line, markOpen) {
		t.Errorf("line = %q, want the open mark", line)
	}
	if !strings.Contains(line, "179") {
		t.Errorf("line = %q, want the number, which is the handle you can type", line)
	}
}

func TestTreeLine_ContinuationBarOnlyOnLevelsThatKeepGoing(t *testing.T) {
	_, byID := indexed(treeItems())

	kept := treeLine(graph.Row{ID: "c", Depth: 2, Last: []bool{false, true}, Parent: "b"}, byID)
	cleared := treeLine(graph.Row{ID: "c", Depth: 2, Last: []bool{true, true}, Parent: "b"}, byID)

	if !strings.HasPrefix(kept, "│   └── ") {
		t.Errorf("line = %q, want the ancestor level to keep its bar", kept)
	}
	if !strings.HasPrefix(cleared, "    └── ") {
		t.Errorf("line = %q, want the ancestor level cleared to spaces", cleared)
	}
}

func TestTreeLine_CompletedItemGetsItsOwnMark(t *testing.T) {
	_, byID := indexed(treeItems())

	line := treeLine(graph.Row{ID: "c", Depth: 0}, byID)

	if !strings.Contains(line, markCompleted) {
		t.Errorf("line = %q, want the completed mark — a finished item stays in the tree", line)
	}
}

func TestTreeLine_MarksASubtreeAlreadyDrawnHigherUp(t *testing.T) {
	_, byID := indexed(treeItems())

	line := treeLine(graph.Row{ID: "b", Depth: 1, Last: []bool{true}, Parent: "a", Repeated: true}, byID)

	if !strings.HasSuffix(line, "(*)") {
		t.Errorf("line = %q, want the (*) marker cargo tree and uv tree both use", line)
	}
}

// The edges no single project's list can show, because neither end of them is
// visible from the other's project.
func TestCrossProjectTag_NamesOnlyTheEdgeThatLeavesItsParentsProjects(t *testing.T) {
	items := treeItems()
	child, parent := items[1], items[0] // 179 in day, under 181 in Home Assistant
	sibling := items[2]                 // 178 in day, under 179 in day

	if tag := crossProjectTag(child, parent, true); tag != day().Name {
		t.Errorf("tag = %q, want the project the dependency lands in", tag)
	}
	if tag := crossProjectTag(sibling, child, true); tag != "" {
		t.Errorf("tag = %q, want none — both ends share a project", tag)
	}
	if tag := crossProjectTag(child, api.ProjectItem{}, false); tag != "" {
		t.Errorf("tag = %q, want none at a root", tag)
	}
}

func TestSelectComponents_HidesATreeWithNoOpenWork(t *testing.T) {
	items := []api.ProjectItem{
		{ID: "done-a", Number: 1, Completed: true, DependencyIDs: []string{"done-b"}},
		{ID: "done-b", Number: 2, Completed: true},
		{ID: "live-a", Number: 3, DependencyIDs: []string{"live-b"}},
		{ID: "live-b", Number: 4},
	}
	g, byID := indexed(items)

	open := selectComponents(g.Components(), byID, "", "", nil)
	all := selectComponents(g.Components(), byID, api.ItemStatusAll, "", nil)

	if len(open) != 1 || len(open[0]) != 2 || open[0][0] != "live-a" {
		t.Errorf("default = %v, want only the tree with open work", open)
	}
	if len(all) != 2 {
		t.Errorf("--status all = %v, want both trees", all)
	}
}

// A row cannot be dropped without orphaning what hangs below it, so a filter
// that matches one item keeps the whole tree it sits in.
func TestSelectComponents_RepoFilterKeepsTheWholeTreeNotJustTheTaggedItem(t *testing.T) {
	dotfiles := "dotfiles"
	items := []api.ProjectItem{
		{ID: "a", Number: 1, Repo: &dotfiles, DependencyIDs: []string{"b"}},
		{ID: "b", Number: 2},
	}
	g, byID := indexed(items)

	kept := selectComponents(g.Components(), byID, "", "", &dotfiles)

	if len(kept) != 1 || len(kept[0]) != 2 {
		t.Errorf("kept = %v, want both items — b carries no repo and still belongs to the tree", kept)
	}
}

func TestSelectComponents_ProjectFilterMatchesOnName(t *testing.T) {
	items := []api.ProjectItem{
		{ID: "a", Number: 1, Projects: []api.Project{day()}, DependencyIDs: []string{"b"}},
		{ID: "b", Number: 2, Projects: []api.Project{day()}},
		{ID: "c", Number: 3, Projects: []api.Project{home()}, DependencyIDs: []string{"d"}},
		{ID: "d", Number: 4, Projects: []api.Project{home()}},
	}
	g, byID := indexed(items)

	kept := selectComponents(g.Components(), byID, "", day().Name, nil)

	if len(kept) != 1 || kept[0][0] != "a" {
		t.Errorf("kept = %v, want only the day tree", kept)
	}
}

func TestResolveFetchedItem_TakesTheNumberOrTheUUID(t *testing.T) {
	items := treeItems()

	byNumber, err := resolveFetchedItem(items, "179")
	if err != nil || byNumber.ID != "b" {
		t.Errorf("resolve(179) = %v, %v; want item b", byNumber.ID, err)
	}
	byID, err := resolveFetchedItem(items, "b")
	if err != nil || byID.Number != 179 {
		t.Errorf("resolve(b) = %v, %v; want number 179", byID.Number, err)
	}
	if _, err := resolveFetchedItem(items, "9999"); err == nil {
		t.Error("resolve(9999) succeeded, want an error naming where to find the numbers")
	}
}

func TestTreeForItem_RootsTheDrawingAtTheItemYouNamed(t *testing.T) {
	g, byID := indexed(treeItems())

	forward, connected := treeForItem(g, "b") // 179, with 181 above it and 178 below
	if !connected {
		t.Fatal("179 reported as having no edges")
	}
	if len(forward.roots) != 1 || forward.roots[0] != "b" {
		t.Errorf("roots = %v, want [b] — naming an item puts it on top", forward.roots)
	}

	drawn := g.Rows(forward.roots, false, graph.Unlimited)
	if len(drawn) != 2 {
		t.Errorf("forward rows = %d, want 2 — 179 and what it waits on, not the whole component", len(drawn))
	}
	if drawn[0].ID != "b" || byID[drawn[1].ID].Number != 178 {
		t.Errorf("forward rows = %v, want 179 then 178", drawn)
	}

	up := g.Rows(forward.roots, true, graph.Unlimited)
	if len(up) != 2 || byID[up[1].ID].Number != 181 {
		t.Errorf("inverted rows = %v, want 179 then the 181 it unblocks", up)
	}
}

func TestTreeForItem_AnItemWithNoEdgesReportsItselfUnconnected(t *testing.T) {
	g, _ := indexed([]api.ProjectItem{{ID: "lonely", Number: 1}})

	tree, connected := treeForItem(g, "lonely")

	if connected {
		t.Error("connected = true, want false — the item has no edges")
	}
	if len(tree.members) != 1 || tree.members[0] != "lonely" {
		t.Errorf("members = %v, want the item alone so --json still returns it", tree.members)
	}
}

// cli-design.md § "A fact on screen is reachable through some machine door":
// every row the drawing shows has to come back through --json.
func TestBuildTreeJSON_CarriesEveryNodeTheDrawingShows(t *testing.T) {
	g, byID := indexed(treeItems())

	doc := buildTreeJSON(g, byID, allTrees(g, false), false, graph.Unlimited)

	if len(doc.Nodes) != 3 {
		t.Errorf("nodes = %d, want 3", len(doc.Nodes))
	}
	if len(doc.Edges) != 2 {
		t.Errorf("edges = %d, want 2", len(doc.Edges))
	}
	if len(doc.Roots) != 1 || doc.Roots[0] != 181 {
		t.Errorf("roots = %v, want [181]", doc.Roots)
	}
	for _, n := range doc.Nodes {
		if n.Number == 178 && n.Status != api.ItemStatusCompleted {
			t.Errorf("178 status = %q, want completed", n.Status)
		}
	}
}

// Inverting is a rendering choice. Re-pointing the edges would hand a consumer
// a graph that contradicts the one the API holds.
func TestBuildTreeJSON_EdgesKeepTheStoredDirectionUnderInvert(t *testing.T) {
	g, byID := indexed(treeItems())

	forward := buildTreeJSON(g, byID, allTrees(g, false), false, graph.Unlimited)
	inverted := buildTreeJSON(g, byID, allTrees(g, true), true, graph.Unlimited)

	if len(forward.Edges) != len(inverted.Edges) {
		t.Fatalf("edge counts differ: %d vs %d", len(forward.Edges), len(inverted.Edges))
	}
	for i := range forward.Edges {
		if forward.Edges[i] != inverted.Edges[i] {
			t.Errorf("edge %d flipped under --invert: %+v vs %+v", i, forward.Edges[i], inverted.Edges[i])
		}
	}
	if len(inverted.Roots) != 1 || inverted.Roots[0] != 178 {
		t.Errorf("inverted roots = %v, want [178] — only the roots follow the drawing", inverted.Roots)
	}
}

func TestBuildTreeJSON_EmptySelectionEncodesAsEmptyArraysNotNull(t *testing.T) {
	g, byID := indexed(treeItems())

	doc := buildTreeJSON(g, byID, nil, false, graph.Unlimited)

	if doc.Nodes == nil || doc.Edges == nil || doc.Roots == nil {
		t.Errorf("doc = %+v, want empty arrays — a consumer should not branch on null", doc)
	}
}
