package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func newProjectsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "projects",
		Short: "List, inspect, and manage your projects",
		Long: "Ongoing initiatives, each holding an ordered list of work items. The project\n" +
			"is the container; the work itself is in `icb projects items`.",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newProjectsListCommand(),
		newProjectsViewCommand(),
		newProjectsCreateCommand(),
		newProjectsEditCommand(),
		newProjectsDeleteCommand(),
		newItemsCommand(),
	)
	return cmd
}

func newProjectsListCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List all projects",
		Example: "  icb projects list\n  icb projects list --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			projects, err := client.ListProjects(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), projects)
			}
			printProjectsTable(cmd.OutOrStdout(), projects)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output projects as JSON to stdout")
	return cmd
}

func newProjectsViewCommand() *cobra.Command {
	var (
		asJSON   bool
		archived bool
	)
	cmd := &cobra.Command{
		Use:     "view <project-id>",
		Short:   "Show a project and its items",
		Example: "  icb projects view 018f...\n  icb projects view 018f... --archived --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			project, err := client.GetProject(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			items, err := client.ListProjectItems(cmd.Context(), args[0], archived)
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
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the project and items as JSON to stdout")
	cmd.Flags().BoolVar(&archived, "archived", false, "Include archived items")
	return cmd
}

func newProjectsCreateCommand() *cobra.Command {
	var (
		name        string
		description string
		position    int
		asJSON      bool
	)
	cmd := &cobra.Command{
		Use:     "create --name <name> [flags]",
		Short:   "Create a new project",
		Example: "  icb projects create --name \"Personal OS unification\"",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return usageError{errors.New("--name is required")}
			}
			in := api.ProjectCreateInput{Name: name}
			if cmd.Flags().Changed("description") {
				in.Description = &description
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
	cmd.Flags().IntVar(&position, "position", 0, "Sort position among projects")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created project as JSON to stdout")
	return cmd
}

func newProjectsEditCommand() *cobra.Command {
	var (
		name        string
		description string
		position    int
		asJSON      bool
	)
	cmd := &cobra.Command{
		Use:     "edit <project-id> [flags]",
		Short:   "Change fields on an existing project",
		Long:    "Update only the fields whose flags you pass; everything else is left unchanged.",
		Example: "  icb projects edit 018f... --name \"New name\" --position 2",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ProjectUpdateInput{}
			if f.Changed("name") {
				in.Name = &name
			}
			if f.Changed("description") {
				in.Description = &description
			}
			if f.Changed("position") {
				in.Position = &position
			}
			if in == (api.ProjectUpdateInput{}) {
				return usageError{errors.New("nothing to change — pass at least one of --name/--description/--position")}
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
	cmd.Flags().IntVar(&position, "position", 0, "New sort position")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated project as JSON to stdout")
	return cmd
}

func newProjectsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:   "delete <project-id>",
		Short: "Delete a project",
		Long: "Permanently delete a project. The API auto-removes completed items that\n" +
			"belong only to this project, and refuses (409) if incomplete items would be\n" +
			"orphaned. Prompts for confirmation unless --yes.",
		Example: "  icb projects delete 018f...\n  icb projects delete 018f... --yes",
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
				prompt := fmt.Sprintf("Delete project %q (%s items)? This cannot be undone.", project.Name, itemCount(project))
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(), prompt)
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

func printProjectsTable(out io.Writer, projects []api.Project) {
	if len(projects) == 0 {
		_, _ = fmt.Fprintln(out, "No projects yet. Create one with `icb projects create --name ...`.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tNAME\tITEMS\tPOS")
	for _, p := range projects {
		_, _ = fmt.Fprintf(tw, "%s\t%s\t%s\t%d\n", p.ID, p.Name, itemCount(p), p.Position)
	}
	_ = tw.Flush()
}

func printProjectDetail(out io.Writer, p api.Project, items []api.ProjectItemInProject) {
	_, _ = fmt.Fprintf(out, "%s\n", p.Name)
	_, _ = fmt.Fprintf(out, "  id:        %s\n", p.ID)
	if d := strValue(p.Description); d != "" {
		_, _ = fmt.Fprintf(out, "  desc:      %s\n", d)
	}
	_, _ = fmt.Fprintf(out, "  position:  %d\n", p.Position)
	_, _ = fmt.Fprintf(out, "  items:     %s\n", itemCount(p))

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
		_, _ = fmt.Fprintf(tw, "  %d\t%s\t%s\t%s\n", it.Position, itemStatus(it), it.Title, it.ID)
	}
	_ = tw.Flush()
}

func itemStatus(it api.ProjectItemInProject) string {
	switch {
	case it.Archived:
		return "archived"
	case it.Completed:
		return "done"
	default:
		return "open"
	}
}

// itemCount renders a project's item count, or "—" when the server omitted it
// (create/update responses carry no count).
func itemCount(p api.Project) string {
	if p.ItemCount == nil {
		return "—"
	}
	return fmt.Sprintf("%d", *p.ItemCount)
}

// strValue dereferences a nullable string field to its value, or "" when nil.
func strValue(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}
