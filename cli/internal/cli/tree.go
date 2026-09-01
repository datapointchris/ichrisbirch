package cli

import (
	"fmt"
	"io"
	"strconv"
	"strings"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/graph"
)

// The marks a tree row carries for an item's state. The same three todoui draws,
// because both front doors render the same rows and a reader should not have to
// learn two vocabularies for one fact.
const (
	markOpen      = "○"
	markCompleted = "✓"
	markArchived  = "▪"
)

func newItemsTreeCommand() *cobra.Command {
	var (
		asJSON     bool
		invert     bool
		depth      int
		project    string
		repo       string
		itemStatus string
	)
	cmd := &cobra.Command{
		Use:   "tree [<item>]",
		Short: "Draw the dependency trees, or the one an item sits in",
		Long: "Name an item to draw the tree it belongs to. Name nothing to draw every\n" +
			"tree. Items with no dependencies either way are not in any tree and do\n" +
			"not appear.\n" +
			"\n" +
			"A child is something its parent is waiting on. --invert reads the edges\n" +
			"the other way, so the children become the work the root unblocks — the\n" +
			"better view of anything several items are queued behind.\n" +
			"\n" +
			"--status, --project and --repo select which TREES are drawn, not which\n" +
			"rows appear inside one. A row cannot be dropped without orphaning\n" +
			"everything below it, so a tree is kept when any of its items matches and\n" +
			"is then drawn whole. A tree with no open work is hidden by default;\n" +
			"finished ones accumulate and would otherwise fill the page with history.\n" +
			"\n" +
			"A dependency that leaves the parent's projects is tagged with the project\n" +
			"it lands in, since that edge is invisible from either project's own list.\n" +
			"\n" +
			"(*) marks an item whose dependencies were already drawn higher up, the\n" +
			"convention cargo tree and uv tree both use.",
		Example: "  icb projects items tree\n" +
			"  icb projects items tree 179\n" +
			"  icb projects items tree 179 --invert\n" +
			"  icb projects items tree --repo dotfiles\n" +
			"  icb projects items tree --status all --json",
		Args: usageArgs(cobra.MaximumNArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if err := validateItemStatus(cmd, itemStatus); err != nil {
				return err
			}
			if depth < 0 {
				return usageError{fmt.Errorf("--depth cannot be negative")}
			}
			maxDepth := graph.Unlimited
			if cmd.Flags().Changed("depth") {
				maxDepth = depth
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			// Always every item, whatever the flags narrow to. An edge crosses
			// the status and project boundaries freely, and a finished item
			// sitting mid-chain is what joins the two halves either side of it,
			// so fetching a subset severs edges and splits one tree into
			// several without saying it did.
			items, err := client.ListItems(cmd.Context(), nil, api.ItemStatusAll, api.DateBounds{}, nil)
			if err != nil {
				return handleAPIError(err)
			}

			byID := make(map[string]api.ProjectItem, len(items))
			nodes := make([]graph.Node, 0, len(items))
			for _, it := range items {
				byID[it.ID] = it
				nodes = append(nodes, graph.Node{ID: it.ID, Order: it.Number, Deps: it.DependencyIDs})
			}
			g := graph.Build(nodes)

			var trees []drawTree
			if len(args) == 1 {
				item, err := resolveFetchedItem(items, args[0])
				if err != nil {
					return err
				}
				tree, connected := treeForItem(g, item.ID)
				if !connected {
					_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "Item %d has no dependencies either way.\n", item.Number)
				}
				trees = []drawTree{tree}
			} else {
				for _, members := range selectComponents(g.Components(), byID, itemStatus, project, repoFlagValue(cmd, repo)) {
					trees = append(trees, drawTree{roots: g.Roots(members, invert), members: members})
				}
			}

			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), buildTreeJSON(g, byID, trees, invert, maxDepth))
			}
			printTrees(cmd.OutOrStdout(), g, byID, trees, invert, maxDepth)
			hintHiddenTrees(cmd, asJSON, len(args) == 1)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the nodes and edges as JSON to stdout")
	cmd.Flags().BoolVar(&invert, "invert", false, "Draw what each item unblocks instead of what it waits on")
	cmd.Flags().IntVar(&depth, "depth", 0, "Stop drawing below this many levels (default every level)")
	cmd.Flags().StringVar(&project, "project", "", "Only trees holding an item in this project")
	cmd.Flags().StringVar(&repo, "repo", "", "Only trees holding an item tagged with this repo (empty string for untagged work)")
	cmd.Flags().StringVar(&itemStatus, "status", "", "Keep trees holding an item in this state: "+strings.Join(api.ItemStatuses, ", ")+" (default open)")
	return cmd
}

// resolveFetchedItem finds the item the argument names among the ones already
// fetched. The API resolves a number or a UUID server-side, but the tree holds
// every item in memory by the time it needs one, so a lookup request here would
// buy nothing.
func resolveFetchedItem(items []api.ProjectItem, ref string) (api.ProjectItem, error) {
	if number, err := strconv.Atoi(ref); err == nil {
		for _, it := range items {
			if it.Number == number {
				return it, nil
			}
		}
	}
	for _, it := range items {
		if it.ID == ref {
			return it, nil
		}
	}
	return api.ProjectItem{}, fmt.Errorf("no item %q — `icb projects items list` shows the numbers", ref)
}

// treeForItem roots the drawing at the item that was named, whichever way the
// edges are read. Forward that is what the item waits on, inverted it is what
// finishing it releases; starting from the component's own ends instead would
// answer neither question about the item you asked about. The bool reports
// whether the item has any edge at all.
func treeForItem(g *graph.Graph, id string) (drawTree, bool) {
	members := g.ComponentOf(id)
	if members == nil {
		return drawTree{roots: []string{id}, members: []string{id}}, false
	}
	return drawTree{roots: []string{id}, members: members}, true
}

// selectComponents keeps a tree when any of its items answers the filters. The
// status default is open, matching every other item read.
func selectComponents(components [][]string, byID map[string]api.ProjectItem, itemStatus, project string, repo *string) [][]string {
	if itemStatus == "" {
		itemStatus = api.ItemStatusOpen
	}
	kept := make([][]string, 0, len(components))
	for _, members := range components {
		if componentMatches(members, byID, itemStatus, project, repo) {
			kept = append(kept, members)
		}
	}
	return kept
}

func componentMatches(members []string, byID map[string]api.ProjectItem, itemStatus, project string, repo *string) bool {
	statusOK, projectOK, repoOK := itemStatus == api.ItemStatusAll, project == "", repo == nil
	for _, id := range members {
		item := byID[id]
		if !statusOK && flatItemStatus(item) == itemStatus {
			statusOK = true
		}
		if !projectOK {
			for _, p := range item.Projects {
				if p.Name == project {
					projectOK = true
					break
				}
			}
		}
		if !repoOK && strValue(item.Repo) == *repo {
			repoOK = true
		}
	}
	return statusOK && projectOK && repoOK
}

func hintHiddenTrees(cmd *cobra.Command, asJSON, scoped bool) {
	if asJSON || scoped || cmd.Flags().Changed("status") {
		return
	}
	_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "\nTrees with no open work are hidden: %s --status all\n", cmd.CommandPath())
}

// --- Rendering ---

// drawTree is one drawing: where the walk starts, and the items that bound what
// the machine rendering may carry.
type drawTree struct {
	roots   []string
	members []string
}

func printTrees(out io.Writer, g *graph.Graph, byID map[string]api.ProjectItem, trees []drawTree, invert bool, maxDepth int) {
	if len(trees) == 0 {
		_, _ = fmt.Fprintln(out, "No dependency trees.")
		return
	}
	for i, tree := range trees {
		if i > 0 {
			_, _ = fmt.Fprintln(out)
		}
		for _, row := range g.Rows(tree.roots, invert, maxDepth) {
			_, _ = fmt.Fprintln(out, treeLine(row, byID))
		}
	}
}

func treeLine(row graph.Row, byID map[string]api.ProjectItem) string {
	item := byID[row.ID]
	var b strings.Builder
	for i, last := range row.Last {
		switch {
		case i < len(row.Last)-1 && last:
			b.WriteString("    ")
		case i < len(row.Last)-1:
			b.WriteString("│   ")
		case last:
			b.WriteString("└── ")
		default:
			b.WriteString("├── ")
		}
	}
	b.WriteString(itemMark(item))
	b.WriteString(" ")
	b.WriteString(strconv.Itoa(item.Number))
	b.WriteString(" ")
	b.WriteString(item.Title)
	if tag := crossProjectTag(item, byID[row.Parent], row.Parent != ""); tag != "" {
		b.WriteString(" [")
		b.WriteString(tag)
		b.WriteString("]")
	}
	if row.Repeated {
		b.WriteString(" (*)")
	}
	return b.String()
}

func itemMark(item api.ProjectItem) string {
	switch {
	case item.Archived:
		return markArchived
	case item.Completed:
		return markCompleted
	default:
		return markOpen
	}
}

// crossProjectTag names where a dependency lands when it shares no project with
// the item waiting on it. Those edges are the ones neither project's own list
// can show, and they are rare enough that tagging every edge would bury them.
func crossProjectTag(item, parent api.ProjectItem, hasParent bool) string {
	if !hasParent || len(item.Projects) == 0 {
		return ""
	}
	for _, p := range item.Projects {
		for _, q := range parent.Projects {
			if p.Name == q.Name {
				return ""
			}
		}
	}
	return item.Projects[0].Name
}

// --- JSON ---

// treeDocument is the machine rendering: the nodes and the edges between them,
// never the drawing. Everything the drawing shows is derivable from it, and a
// consumer wanting a different shape — a graphviz file, a different traversal —
// does not have to parse box-drawing characters to get it.
type treeDocument struct {
	Nodes []treeNode `json:"nodes"`
	Edges []treeEdge `json:"edges"`
	Roots []int      `json:"roots"`
}

type treeNode struct {
	ID       string   `json:"id"`
	Number   int      `json:"number"`
	Title    string   `json:"title"`
	Status   string   `json:"status"`
	Repo     *string  `json:"repo"`
	Projects []string `json:"projects"`
}

// treeEdge always runs from the item to the thing it depends on, whichever way
// the drawing was asked to run. Only Roots reflects --invert.
type treeEdge struct {
	Item      int `json:"item"`
	DependsOn int `json:"depends_on"`
}

func buildTreeJSON(g *graph.Graph, byID map[string]api.ProjectItem, trees []drawTree, invert bool, maxDepth int) treeDocument {
	doc := treeDocument{Nodes: []treeNode{}, Edges: []treeEdge{}, Roots: []int{}}
	for _, tree := range trees {
		drawn := make(map[string]bool)
		for _, row := range g.Rows(tree.roots, invert, maxDepth) {
			drawn[row.ID] = true
		}
		for _, id := range tree.members {
			if !drawn[id] {
				continue
			}
			item := byID[id]
			projects := make([]string, 0, len(item.Projects))
			for _, p := range item.Projects {
				projects = append(projects, p.Name)
			}
			doc.Nodes = append(doc.Nodes, treeNode{
				ID:       item.ID,
				Number:   item.Number,
				Title:    item.Title,
				Status:   flatItemStatus(item),
				Repo:     item.Repo,
				Projects: projects,
			})
		}
		for _, edge := range g.Edges(tree.members) {
			if !drawn[edge[0]] || !drawn[edge[1]] {
				continue
			}
			doc.Edges = append(doc.Edges, treeEdge{Item: byID[edge[0]].Number, DependsOn: byID[edge[1]].Number})
		}
		for _, root := range tree.roots {
			doc.Roots = append(doc.Roots, byID[root].Number)
		}
	}
	return doc
}
