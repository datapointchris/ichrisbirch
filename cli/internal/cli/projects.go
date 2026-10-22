package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/datapointchris/goclikit"
	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/repos"
)

// projectHints is the command that finds a valid project name. The items
// subcommands take a project name too, so their own hints name it as well.
//
// A name resolves whatever the project's status, so a miss is a name that did
// not match in full, never a project hidden by status. The API names the
// projects near the miss on the line above these.
var projectHints = []string{
	"A project is named in full or by its id; every project: icb projects list --status all",
	"A development project is an issue initiative: icb issues list --initiative <name>",
}

func newProjectsCommand() *cobra.Command {
	cmd := goclikit.AsNamespace(&cobra.Command{
		Use:   "projects",
		Short: "List, inspect, and manage your projects",
		Long: "Personal projects, each holding an ordered list of work items. The project\n" +
			"is the container; the work itself is in `icb projects items`. Development\n" +
			"work is `icb issues`.\n" +
			"\n" +
			"<project> and --project take a project's full name or its id, whatever its\n" +
			"status. A name that misses is answered with the names near it.",
	})
	goclikit.WithRecoveryHints(cmd, projectHints...)
	splitReadingFromChanging(cmd)
	cmd.AddGroup(&cobra.Group{ID: groupProjectItems, Title: "Item commands:"})
	cmd.AddCommand(inGroup(groupReading,
		newProjectsListCommand(),
		newProjectsNextCommand(),
		newProjectsShowCommand(),
	)...)
	cmd.AddCommand(inGroup(groupChanging,
		newProjectsCreateCommand(),
		newProjectsEditCommand(),
		newProjectsShelveCommand(),
		newProjectsCompleteCommand(),
		newProjectsDropCommand(),
		newProjectsReopenCommand(),
		newProjectsDeleteCommand(),
	)...)
	cmd.AddCommand(inGroup(groupProjectItems, newItemsCommand())...)
	return cmd
}

func newProjectsListCommand() *cobra.Command {
	var (
		asJSON        bool
		repo          string
		projectStatus string
		limit         int
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List the active projects",
		Long: "The active projects, with the repos their items touch. --repo narrows to the\n" +
			"projects holding work on one repo — the efforts that span it, however they are\n" +
			"named. Shelved, completed and dropped projects are hidden until --status\n" +
			"asks for them.\n" +
			"\n" +
			"--limit caps what the filters left, so it takes the first projects in\n" +
			"position order rather than filtering a capped slice.",
		Example: "  icb projects list\n  icb projects list --repo dotfiles\n" +
			"  icb projects list --limit 5\n" +
			"  icb projects list --status completed\n  icb projects list --status all --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			filter, err := repoFlagValue(cmd, repo)
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			projects, err := client.ListProjects(cmd.Context(), filter, projectStatus, limitFlag(cmd))
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), projects)
			}
			// "No projects yet, create one" is true of an empty database and a
			// lie about a filter that matched nothing.
			if len(projects) == 0 && filter != nil {
				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "No projects hold work on repo %s.\n", *filter)
				return nil
			}
			if len(projects) == 0 && projectStatus != "" && projectStatus != api.ProjectStatusAll {
				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "No %s projects.\n", projectStatus)
				return nil
			}
			// The status column earns its width only when the rows can differ in
			// it, which the flag decides — no second request to find out.
			printProjectsTable(cmd.OutOrStdout(), projects, projectStatus != "")
			if projectStatus == "" {
				_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nShelved, completed and dropped projects are hidden: icb projects list --status all")
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output projects as JSON to stdout")
	cmd.Flags().StringVar(&repo, "repo", "", "Only projects holding work on this repo")
	cmd.Flags().StringVar(&projectStatus, "status", "", "One of: "+strings.Join(api.ProjectStatuses, ", ")+" (default active)")
	addLimitFlag(cmd, &limit)
	return cmd
}

// defaultNextItemLimit caps the items `projects next` prints. The ordering is
// the point of the verb, so the head of the list is the answer and the tail is
// context; a caller who wants more names a larger number.
const defaultNextItemLimit = 10

// newProjectsNextCommand prints the focus project, as focusQueue picks it, and
// its open items in the order they are taken. The head is the next thing to do,
// which is what a caller asking for `--limit 1` wants. `icb overview` shows the
// same project and items, and --json answers with the overview's section.
//
// --kind narrows the focus to projects of one kind, so a question about making
// things never resolves to an errand filed as a project. The filter runs
// client-side because every item already carries its projects, so kind rides
// along and the alternative would be a query parameter that saves no round trip.
func newProjectsNextCommand() *cobra.Command {
	var (
		asJSON bool
		kind   string
		repo   string
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "next",
		Short: "The project in focus and its open items, in the order to take them",
		Long: "Projects are worked one at a time. The focus is the highest-ranked active project\n" +
			"holding an open item. It is printed with its items in their position order, so\n" +
			"the first row is the next thing to do. No other project appears until it is\n" +
			"completed or moved down with `icb projects edit <project> --position <n>`.\n" +
			"\n" +
			"If every open item in the focus project is blocked, it keeps the focus and its\n" +
			"blocked items are listed instead. An item in several projects belongs to the\n" +
			"highest-ranked active one. `icb overview` shows the same project.",
		Example: "  icb projects next\n" +
			"  icb projects next --kind chore\n" +
			"  icb projects next --repo ichrisbirch\n" +
			"  icb projects next --limit 1 --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			filter, err := repoFlagValue(cmd, repo)
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			// Every open item, uncapped: the blocked set is computed from the
			// whole graph, and --limit here caps what is printed rather than
			// what is read.
			all, err := client.ListItems(cmd.Context(), filter, api.ItemStatusOpen, api.Window{}, nil)
			if err != nil {
				return handleAPIError(err)
			}
			// Blocked is deliberately unfiltered: an item is blocked by whatever
			// blocks it, and a blocker in another repo still blocks. Filtering
			// here would present blocked work as actionable.
			blocked, err := client.ListBlockedItems(cmd.Context(), nil)
			if err != nil {
				return handleAPIError(err)
			}
			focus := focusQueue(all, blocked, kind)
			items := capItems(focus.Next, limit)
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), projectItemSection{
					Project:      focus.Project,
					Next:         items,
					NextTotal:    len(focus.Next),
					Blocked:      capItems(focus.Blocked, limit),
					BlockedTotal: len(focus.Blocked),
				})
			}
			out := cmd.OutOrStdout()
			// The sentences describe the data, so they read the uncapped set. A
			// --limit the caller chose is not a fact about what is outstanding, and
			// gating on the capped slice reported an empty subject for --limit 0
			// against every open item there is.
			if focus.Project == nil {
				switch {
				case kind != "":
					_, _ = fmt.Fprintf(out, "No open items in %s projects.\n", kind)
				case filter != nil:
					_, _ = fmt.Fprintf(out, "No open items for repo %s.\n", *filter)
				default:
					_, _ = fmt.Fprintln(out, "No items.")
				}
				return nil
			}
			if len(focus.Next) == 0 {
				_, _ = fmt.Fprintf(out, "%s: nothing to take, every open item is blocked.\n", focus.Project.Name)
				printItemsTable(out, focus.Blocked)
				return nil
			}
			// A zero cap prints nothing, the way `head -n 0` does.
			if len(items) == 0 {
				return nil
			}
			_, _ = fmt.Fprintln(out, focus.Project.Name)
			printQueueTable(out, items)
			noteCappedRows(cmd, len(items), len(focus.Next))
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the project and its items as JSON to stdout")
	cmd.Flags().StringVar(&kind, "kind", "", "Only projects of this kind: "+strings.Join(api.ProjectKinds, ", "))
	cmd.Flags().StringVar(&repo, "repo", "", "Only items tagged with this repo (empty string for untagged work)")
	addCapFlag(cmd, &limit, defaultNextItemLimit, "Maximum number of items to show")
	return cmd
}

// newProjectsCompleteCommand and its siblings are a PATCH of `status`. There are
// no complete/drop/reopen action endpoints: one write path means one place
// validating the transition and deriving closed_at from it.
func newProjectsCompleteCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "complete <project>",
		Short: "Mark a project finished, which hides it",
		Long: "A project is a finite effort with a definition of done, so completing it is\n" +
			"what takes it out of the list — there is no separate archive step. Its items\n" +
			"are left exactly as they are: an item still open when the project finished was\n" +
			"still open, and that is worth knowing.",
		Example: "  icb projects complete clisteno",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			completed := api.ProjectStatusCompleted
			return runProjectUpdate(cmd, args[0], api.ProjectUpdateInput{Status: &completed}, asJSON, "Completed")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated project as JSON to stdout")
	return cmd
}

func newProjectsDropCommand() *cobra.Command {
	var (
		reason string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "drop <project> --reason <why>",
		Short: "Close a project you are not going to do",
		Long: "For the projects that end without being finished. --reason is required, and\n" +
			"that is the point: \"deferred\" invites the same idea back next month, whereas\n" +
			"dropped-and-here-is-why closes the question.",
		Example: "  icb projects drop \"Rewrite in Rust\" --reason \"Go covers it and I know Go\"",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if reason == "" {
				return goclikit.UsageError(errors.New("--reason is required — say why it is dropped rather than deferred"))
			}
			dropped := "dropped"
			in := api.ProjectUpdateInput{Status: &dropped, StatusReason: &reason}
			return runProjectUpdate(cmd, args[0], in, asJSON, "Dropped")
		},
	}
	cmd.Flags().StringVar(&reason, "reason", "", "Why it is dropped rather than deferred (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated project as JSON to stdout")
	return cmd
}

func newProjectsShelveCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "shelve <project>",
		Short: "Set a project aside for someday, which hides it",
		Long: "For a project you still mean to do, just not now. It moves to --status\n" +
			"someday, out of the active list, and no close is recorded. Its items keep\n" +
			"their state. One in no other active project leaves `icb projects next`\n" +
			"until this one returns. It also gives up its name, so a new project may take\n" +
			"it, and bringing this one back is then refused until one of the two is\n" +
			"renamed. `icb projects reopen` returns it to the active list.",
		Example: "  icb projects shelve \"Home Building Projects\"",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			someday := api.ProjectStatusSomeday
			return runProjectUpdate(cmd, args[0], api.ProjectUpdateInput{Status: &someday}, asJSON, "Shelved")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated project as JSON to stdout")
	return cmd
}

func newProjectsReopenCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "reopen <project>",
		Short: "Return a shelved or closed project to the active list",
		Long: "Clears the closing reason and timestamp along with the status. Refused if an\n" +
			"active project has taken the name in the meantime — only one project holds a\n" +
			"name at a time, and it is the live one.",
		Example: "  icb projects reopen \"Kitchen remodel\"",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			active := "active"
			return runProjectUpdate(cmd, args[0], api.ProjectUpdateInput{Status: &active}, asJSON, "Reopened")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated project as JSON to stdout")
	return cmd
}

func runProjectUpdate(cmd *cobra.Command, ref string, in api.ProjectUpdateInput, asJSON bool, verb string) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	project, err := client.UpdateProject(cmd.Context(), ref, in)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), project)
	}
	_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s project %q (%s)\n", verb, project.Name, project.ID)
	return nil
}

func newProjectsShowCommand() *cobra.Command {
	var (
		asJSON     bool
		itemStatus string
	)
	cmd := &cobra.Command{
		Use:     "show <project>",
		Short:   "Show a project and its open items",
		Example: "  icb projects show \"Kitchen remodel\"\n  icb projects show \"Kitchen remodel\" --status all --json",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if err := validateItemStatus(cmd, itemStatus); err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			project, err := client.GetProject(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			items, err := client.ListProjectItems(cmd.Context(), args[0], itemStatus, api.Window{}, nil)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), struct {
					api.Project
					Items []api.ProjectItemInProject `json:"items"`
				}{Project: project, Items: items})
			}
			printProjectDetail(cmd.OutOrStdout(), project, items)
			hintHiddenItems(cmd, asJSON, itemStatus)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the project and items as JSON to stdout")
	cmd.Flags().StringVar(&itemStatus, "status", "", "One of: "+strings.Join(api.ItemStatuses, ", ")+" (default open)")
	return cmd
}

// refuseRepoNamedProject rejects a project name the repo registry knows.
//
// A project name must be bounded work — something that ends. A repo does not
// end, so a project named after one silently becomes the bucket every later
// papercut falls into: it starts as the finite effort of building the thing,
// that effort finishes, and the name outlives it. The repo association is the
// item's `--repo` tag, which already crosses project boundaries and outlives
// any single project, so "what is the dotfiles work" is
// `projects items list --repo dotfiles` rather than a project called dotfiles.
//
// A missing registry bans nothing, matching validateRepoFlag: refusing to file
// work on a machine without a registry is worse than the wrong name.
func refuseRepoNamedProject(name string) error {
	registry, err := repos.Load(repos.DefaultPath())
	if err != nil {
		return err
	}
	if !registry.Knows(name) {
		return nil
	}
	return goclikit.UsageError(fmt.Errorf(
		"%q names a repo, which never ends — name the bounded work instead (\"%s sync improvements\", \"Extract x from %s\") and tag the items with --repo %s",
		name, name, name, name,
	))
}

func newProjectsCreateCommand() *cobra.Command {
	var (
		name        string
		description string
		kind        string
		position    int
		asJSON      bool
	)
	cmd := &cobra.Command{
		Use:   "create --name <name> [flags]",
		Short: "Create a new project",
		Example: "  icb projects create --name \"Kitchen remodel\"\n" +
			"  icb projects create --name \"Sell Unused Shite\" --kind chore\n" +
			"  icb projects create --name \"Reading backlog\" --description \"Books to finish this year\"\n" +
			"  icb projects create --name \"Learn to sail\" --description \"$(cat plan.md)\" --json",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return goclikit.UsageError(errors.New("--name is required"))
			}
			if err := refuseRepoNamedProject(name); err != nil {
				return err
			}
			in := api.ProjectCreateInput{Name: name}
			if cmd.Flags().Changed("description") {
				in.Description = &description
			}
			if cmd.Flags().Changed("kind") {
				in.Kind = &kind
			}
			if cmd.Flags().Changed("position") {
				in.Position = &position
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			project, err := client.CreateProject(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), project)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created project %q (%s)\n", project.Name, project.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Project name (required)")
	cmd.Flags().StringVar(&description, "description", "", "Project description")
	cmd.Flags().StringVar(&kind, "kind", "", "What sort of work this is: "+strings.Join(api.ProjectKinds, ", ")+" (default "+api.ProjectKindLife+")")
	cmd.Flags().IntVar(&position, "position", 0, "Sort position among projects")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created project as JSON to stdout")
	return cmd
}

func newProjectsEditCommand() *cobra.Command {
	var (
		name        string
		description string
		kind        string
		position    int
		asJSON      bool
	)
	cmd := &cobra.Command{
		Use:   "edit <project> [flags]",
		Short: "Change fields on an existing project",
		Long:  "Update only the fields whose flags you pass; everything else is left unchanged.",
		Example: "  icb projects edit \"Kitchen remodel\" --name \"Bathroom remodel\" --position 2\n" +
			"  icb projects edit \"Kitchen remodel\" --kind chore",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ProjectUpdateInput{}
			if f.Changed("name") {
				// Checked on rename too: a ban one `edit` walks around is decoration.
				if err := refuseRepoNamedProject(name); err != nil {
					return err
				}
				in.Name = &name
			}
			if f.Changed("description") {
				in.Description = &description
			}
			if f.Changed("kind") {
				in.Kind = &kind
			}
			if f.Changed("position") {
				in.Position = &position
			}
			if in == (api.ProjectUpdateInput{}) {
				return goclikit.UsageError(errors.New("nothing to change — pass at least one of --name/--description/--kind/--position"))
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			project, err := client.UpdateProject(cmd.Context(), args[0], in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), project)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated project %q (%s)\n", project.Name, project.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New project name")
	cmd.Flags().StringVar(&description, "description", "", "New project description")
	cmd.Flags().StringVar(&kind, "kind", "", "New kind: "+strings.Join(api.ProjectKinds, ", "))
	cmd.Flags().IntVar(&position, "position", 0, "New sort position")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated project as JSON to stdout")
	return cmd
}

func newProjectsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:   "delete <project>",
		Short: "Delete a project",
		Long: "Permanently delete a project. Completed items belonging only to this project\n" +
			"go with it. If incomplete items would be left with no project, the delete is\n" +
			"refused — move them first. Prompts for confirmation unless --yes.",
		Example: "  icb projects delete \"Kitchen remodel\"\n  icb projects delete \"Kitchen remodel\" --yes",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			// Fetch first so the confirmation names the project being destroyed.
			project, err := client.GetProject(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				prompt := fmt.Sprintf("Delete project %q (%s items)? This cannot be undone.", project.Name, count(project.ItemCount))
				ok, err := confirm(cmd, prompt)
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteProject(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted project %q (%s)\n", project.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// encodeJSON writes v as indented JSON — the scripting-friendly output shared by
// every resource command's --json flag.
func encodeJSON(out io.Writer, v any) error {
	enc := json.NewEncoder(out)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

func printProjectsTable(out io.Writer, projects []api.Project, withStatus bool) {
	if len(projects) == 0 {
		_, _ = fmt.Fprintln(out, "No projects yet. Create one with `icb projects create --name ...`.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	header := "ID\tNAME\tKIND\tOPEN\tDONE\tITEMS\tPOS\tREPOS"
	if withStatus {
		header = "ID\tNAME\tKIND\tSTATUS\tOPEN\tDONE\tITEMS\tPOS\tREPOS"
	}
	_, _ = fmt.Fprintln(tw, header)
	for _, p := range projects {
		fields := []any{p.ID, p.Name, p.Kind}
		if withStatus {
			fields = append(fields, p.Status)
		}
		fields = append(fields, count(p.OpenCount), count(p.CompletedCount), count(p.ItemCount), p.Position, repoList(p.Repos))
		_, _ = fmt.Fprintln(tw, joinFields(fields))
	}
	_ = tw.Flush()
}

// joinFields renders a row's already-formatted values tab-separated, so a table
// with an optional column does not need two format strings that can disagree.
func joinFields(fields []any) string {
	rendered := make([]string, len(fields))
	for i, field := range fields {
		rendered[i] = fmt.Sprint(field)
	}
	return strings.Join(rendered, "\t")
}

// closedSuffix dates a terminal status. Nothing for an active project, which has
// no closing date and would otherwise print an empty parenthesis.
func closedSuffix(p api.Project) string {
	if p.ClosedAt == nil {
		return ""
	}
	return " (" + localDay(*p.ClosedAt) + ")"
}

// repoList renders a project's derived repos. An em dash rather than a blank
// keeps the column readable for the projects that are not repo work at all.
func repoList(repos []string) string {
	if len(repos) == 0 {
		return "—"
	}
	return strings.Join(repos, ",")
}

func printProjectDetail(out io.Writer, p api.Project, items []api.ProjectItemInProject) {
	_, _ = fmt.Fprintf(out, "%s\n", p.Name)
	_, _ = fmt.Fprintf(out, "  id:        %s\n", p.ID)
	if d := strValue(p.Description); d != "" {
		_, _ = fmt.Fprintf(out, "  desc:      %s\n", d)
	}
	_, _ = fmt.Fprintf(out, "  kind:      %s\n", p.Kind)
	_, _ = fmt.Fprintf(out, "  status:    %s%s\n", p.Status, closedSuffix(p))
	if reason := strValue(p.StatusReason); reason != "" {
		_, _ = fmt.Fprintf(out, "  reason:    %s\n", reason)
	}
	_, _ = fmt.Fprintf(out, "  position:  %d\n", p.Position)
	_, _ = fmt.Fprintf(out, "  repos:     %s\n", repoList(p.Repos))
	_, _ = fmt.Fprintf(out, "  items:     %s (%s open, %s done)\n", count(p.ItemCount), count(p.OpenCount), count(p.CompletedCount))

	_, _ = fmt.Fprintf(out, "\nItems (%d):\n", len(items))
	if len(items) == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
		return
	}
	printProjectItemsTable(out, items)
}

func printProjectItemsTable(out io.Writer, items []api.ProjectItemInProject) {
	if len(items) == 0 {
		_, _ = fmt.Fprintln(out, "No items.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "  #\tSTATUS\tTITLE\tID")
	for _, it := range items {
		_, _ = fmt.Fprintf(tw, "  %d\t%s\t%s\t%d\n", it.Position, itemStatus(it), it.Title, it.Number)
	}
	_ = tw.Flush()
}

func itemStatus(it api.ProjectItemInProject) string {
	return serverStatus(it.Status, it.Archived, it.Completed)
}

// count renders one of a project's item counts, or "—" when the server omitted
// it (create/update responses carry no counts).
func count(n *int) string {
	if n == nil {
		return "—"
	}
	return strconv.Itoa(*n)
}

// strValue dereferences a nullable string field to its value, or "" when nil.
func strValue(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}
