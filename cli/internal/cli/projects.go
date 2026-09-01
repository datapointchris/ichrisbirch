package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/repos"
)

// projectHints is the command that finds a valid project name. The items
// subcommands take a project name too, so their own hints name it as well.
//
// The two states are named rather than called "closed", because a reader
// following a word --status does not accept gets a second refusal.
var projectHints = []string{"Completed and dropped projects are hidden: icb projects list --status all"}

func newProjectsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "projects",
		Short: "List, inspect, and manage your projects",
		Long: "Ongoing initiatives, each holding an ordered list of work items. The project\n" +
			"is the container; the work itself is in `icb projects items`.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd, projectHints...)
	cmd.AddCommand(
		newProjectsListCommand(),
		newProjectsShowCommand(),
		newProjectsCreateCommand(),
		newProjectsEditCommand(),
		newProjectsCompleteCommand(),
		newProjectsDropCommand(),
		newProjectsReopenCommand(),
		newProjectsDeleteCommand(),
		newItemsCommand(),
	)
	return cmd
}

func newProjectsListCommand() *cobra.Command {
	var (
		asJSON        bool
		repo          string
		projectStatus string
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List the active projects",
		Long: "The active projects, with the repos their items touch. --repo narrows to the\n" +
			"projects holding work on one repo — the efforts that span it, however they are\n" +
			"named. Completed and dropped projects are hidden until you ask for them by\n" +
			"--status; that is the whole point of closing one.",
		Example: "  icb projects list\n  icb projects list --repo dotfiles\n" +
			"  icb projects list --status completed\n  icb projects list --status all --json",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			filter := repoFlagValue(cmd, repo)
			projects, err := client.ListProjects(cmd.Context(), filter, projectStatus)
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
			// The status column earns its width only when the rows can differ in
			// it, which the flag decides — no second request to find out.
			printProjectsTable(cmd.OutOrStdout(), projects, projectStatus != "")
			if projectStatus == "" {
				_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nCompleted and dropped projects are hidden: icb projects list --status all")
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output projects as JSON to stdout")
	cmd.Flags().StringVar(&repo, "repo", "", "Only projects holding work on this repo")
	cmd.Flags().StringVar(&projectStatus, "status", "", "One of: "+strings.Join(api.ProjectStatuses, ", ")+" (default active)")
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
		Args:    usageArgs(cobra.ExactArgs(1)),
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
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if reason == "" {
				return usageError{errors.New("--reason is required — say why it is dropped rather than deferred")}
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

func newProjectsReopenCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "reopen <project>",
		Short: "Return a closed project to the active list",
		Long: "Clears the closing reason and timestamp along with the status. Refused if an\n" +
			"active project has taken the name in the meantime — only one project holds a\n" +
			"name at a time, and it is the live one.",
		Example: "  icb projects reopen ifiles",
		Args:    usageArgs(cobra.ExactArgs(1)),
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
		Example: "  icb projects show todoui\n  icb projects show todoui --status all --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
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
			items, err := client.ListProjectItems(cmd.Context(), args[0], itemStatus, api.DateBounds{})
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
	return usageError{fmt.Errorf(
		"%q names a repo, which never ends — name the bounded work instead (\"%s sync improvements\", \"Extract x from %s\") and tag the items with --repo %s",
		name, name, name, name,
	)}
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
		Example: "  icb projects create --name \"Personal OS unification\"\n" +
			"  icb projects create --name \"Sell Unused Shite\" --kind chore",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return usageError{errors.New("--name is required")}
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
	cmd.Flags().StringVar(&kind, "kind", "", "What sort of work this is: "+strings.Join(api.ProjectKinds, ", ")+" (default "+api.ProjectKindBuild+")")
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
		Example: "  icb projects edit todoui --name \"New name\" --position 2\n" +
			"  icb projects edit todoui --kind chore",
		Args: usageArgs(cobra.ExactArgs(1)),
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
				return usageError{errors.New("nothing to change — pass at least one of --name/--description/--kind/--position")}
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
		Example: "  icb projects delete todoui\n  icb projects delete todoui --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
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
	return " (" + p.ClosedAt.Format("2006-01-02") + ")"
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
	return itemStatusWord(it.Archived, it.Completed)
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
