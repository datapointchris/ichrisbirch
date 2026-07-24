package cli

import (
	"fmt"
	"io"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newItemsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "items",
		Short: "Work with project items — the structured to-do units in projects",
		Long: "Project items are the ordered work units inside projects (todoui's items),\n" +
			"each with sub-tasks, dependencies, and multi-project membership. This is a\n" +
			"different system from the standalone `icb tasks` app. Requires a logged-in\n" +
			"session (`icb auth login`).",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newItemsListCommand(),
		newItemsBlockedCommand(),
		newItemsSearchCommand(),
		newItemsViewCommand(),
		newItemsCreateCommand(),
		newItemsEditCommand(),
		newItemsCompletionCommand("complete", "Mark an item completed", true),
		newItemsCompletionCommand("reopen", "Reopen a completed item", false),
		newItemsArchiveCommand("archive", "Archive an item", true),
		newItemsArchiveCommand("unarchive", "Restore an archived item", false),
		newItemsDeleteCommand(),
		newItemsReorderCommand(),
		newItemsAddProjectCommand(),
		newItemsRemoveProjectCommand(),
		newItemsAddDependencyCommand(),
		newItemsRemoveDependencyCommand(),
		newItemsBlockersCommand(),
		newItemsTasksCommand(),
		newItemsAddTaskCommand(),
		newItemsCompleteTaskCommand(),
		newItemsEditTaskCommand(),
		newItemsRemoveTaskCommand(),
	)
	return cmd
}

// --- Reads over collections ---

func newItemsListCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List all active (non-archived) items",
		Example: "  icb items list\n  icb items list --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.ListItems(cmd.Context())
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	return cmd
}

func newItemsBlockedCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "blocked",
		Short:   "List items with at least one incomplete dependency",
		Example: "  icb items blocked",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.ListBlockedItems(cmd.Context())
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	return cmd
}

func newItemsSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search items by title or notes",
		Example: "  icb items search kitchen",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.SearchItems(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	return cmd
}

func newItemsBlockersCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "blockers <item-id>",
		Short:   "List the incomplete dependencies blocking an item",
		Example: "  icb items blockers 018f...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.GetBlockers(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output blockers as JSON to stdout")
	return cmd
}

// runItemsCollection runs a fetch that returns a []ProjectItem and renders it as
// JSON or a table — the shared body of list/blocked/search/blockers.
func runItemsCollection(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.ProjectItem, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	items, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), items)
	}
	printItemsTable(cmd.OutOrStdout(), items)
	return nil
}

// --- View ---

func newItemsViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <item-id>",
		Short:   "Show an item with its projects, dependencies, tasks, and blockers",
		Example: "  icb items view 018f...\n  icb items view 018f... --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			detail, err := client.GetItem(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			tasks, err := client.ListItemTasks(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			blockers, err := client.GetBlockers(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), struct {
					api.ProjectItemDetail
					Tasks    []api.ProjectItemTask `json:"tasks"`
					Blockers []api.ProjectItem     `json:"blockers"`
				}{ProjectItemDetail: detail, Tasks: tasks, Blockers: blockers})
			}
			printItemDetail(cmd.OutOrStdout(), detail, tasks, blockers)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output everything as JSON to stdout")
	return cmd
}

// --- Create / edit ---

func newItemsCreateCommand() *cobra.Command {
	var (
		title    string
		notes    string
		projects []string
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "create --title <title> --project <project-id> [flags]",
		Short:   "Create a new project item in one or more projects",
		Example: "  icb items create --title \"Ship the CLI\" --project 018f...",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if title == "" {
				return usageError{fmt.Errorf("--title is required")}
			}
			if len(projects) == 0 {
				return usageError{fmt.Errorf("at least one --project is required")}
			}
			in := api.ProjectItemCreateInput{Title: title, ProjectIDs: projects}
			if cmd.Flags().Changed("notes") {
				in.Notes = &notes
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.CreateItem(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), item)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Created item %q (%s)\n", item.Title, item.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "Item title (required)")
	cmd.Flags().StringVar(&notes, "notes", "", "Markdown notes for the item")
	cmd.Flags().StringArrayVar(&projects, "project", nil, "Project id to add the item to (repeatable; at least one)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created item as JSON to stdout")
	return cmd
}

func newItemsEditCommand() *cobra.Command {
	var (
		title  string
		notes  string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "edit <item-id> [flags]",
		Short:   "Change an item's title or notes",
		Long:    "Update only the fields whose flags you pass. Use complete/reopen and\narchive/unarchive for those state changes.",
		Example: "  icb items edit 018f... --title \"New title\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ProjectItemUpdateInput{}
			if f.Changed("title") {
				in.Title = &title
			}
			if f.Changed("notes") {
				in.Notes = &notes
			}
			if in == (api.ProjectItemUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass --title and/or --notes")}
			}
			return runItemUpdate(cmd, args[0], in, asJSON, "Updated")
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "New item title")
	cmd.Flags().StringVar(&notes, "notes", "", "New markdown notes")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

// newItemsCompletionCommand builds the complete/reopen pair — a PATCH of the
// completed flag. Completing is refused by the API (400) while tasks remain.
func newItemsCompletionCommand(verb, short string, completed bool) *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     verb + " <item-id>",
		Short:   short,
		Example: "  icb items " + verb + " 018f...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			flag := completed
			return runItemUpdate(cmd, args[0], api.ProjectItemUpdateInput{Completed: &flag}, asJSON, "Updated")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

// newItemsArchiveCommand builds the archive/unarchive pair — a PATCH of the
// archived flag.
func newItemsArchiveCommand(verb, short string, archived bool) *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     verb + " <item-id>",
		Short:   short,
		Example: "  icb items " + verb + " 018f...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			flag := archived
			return runItemUpdate(cmd, args[0], api.ProjectItemUpdateInput{Archived: &flag}, asJSON, "Updated")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

// runItemUpdate applies a PATCH and renders the result — shared by edit,
// complete/reopen, and archive/unarchive.
func runItemUpdate(cmd *cobra.Command, id string, in api.ProjectItemUpdateInput, asJSON bool, verb string) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	item, err := client.UpdateItem(cmd.Context(), id, in)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), item)
	}
	fmt.Fprintf(cmd.OutOrStdout(), "%s item %q → %s (%s)\n", verb, item.Title, flatItemStatus(item), item.ID)
	return nil
}

func newItemsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <item-id>",
		Short:   "Delete a project item",
		Long:    "Permanently delete an item and its tasks. Prompts for confirmation unless --yes.",
		Example: "  icb items delete 018f... --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.GetItem(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete item %q? This cannot be undone.", item.Title))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteItem(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted item %q (%s)\n", item.Title, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func newItemsReorderCommand() *cobra.Command {
	var (
		project  string
		position int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "reorder <item-id> --project <project-id> --position <n>",
		Short:   "Move an item to a new position within a project",
		Example: "  icb items reorder 018f... --project 018e... --position 2",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if project == "" {
				return usageError{fmt.Errorf("--project is required")}
			}
			if !cmd.Flags().Changed("position") {
				return usageError{fmt.Errorf("--position is required")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.ReorderItem(cmd.Context(), args[0], api.ProjectItemReorderInput{ProjectID: project, Position: position})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), item)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Moved item %q to position %d (%s)\n", item.Title, item.Position, item.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&project, "project", "", "Project id the item is being reordered within (required)")
	cmd.Flags().IntVar(&position, "position", 0, "New position (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the item as JSON to stdout")
	return cmd
}

// --- Membership ---

func newItemsAddProjectCommand() *cobra.Command {
	var (
		project string
		asJSON  bool
	)
	cmd := &cobra.Command{
		Use:     "add-project <item-id> --project <project-id>",
		Short:   "Add an item to another project",
		Example: "  icb items add-project 018f... --project 018e...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if project == "" {
				return usageError{fmt.Errorf("--project is required")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			p, err := client.AddItemToProject(cmd.Context(), args[0], api.ProjectMembershipInput{ProjectID: project})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), p)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Added item %s to project %q (%s)\n", args[0], p.Name, p.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&project, "project", "", "Project id to add the item to (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the project as JSON to stdout")
	return cmd
}

func newItemsRemoveProjectCommand() *cobra.Command {
	var (
		project string
		yes     bool
	)
	cmd := &cobra.Command{
		Use:     "remove-project <item-id> --project <project-id>",
		Short:   "Remove an item from a project",
		Long:    "Remove an item from a project. The API refuses (409) to remove it from its\nlast project — delete the item instead.",
		Example: "  icb items remove-project 018f... --project 018e...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if project == "" {
				return usageError{fmt.Errorf("--project is required")}
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Remove item %s from project %s?", args[0], project))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if err := client.RemoveItemFromProject(cmd.Context(), args[0], project); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Removed item %s from project %s\n", args[0], project)
			return nil
		},
	}
	cmd.Flags().StringVar(&project, "project", "", "Project id to remove the item from (required)")
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// --- Dependencies ---

func newItemsAddDependencyCommand() *cobra.Command {
	var (
		dependsOn string
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "add-dependency <item-id> --depends-on <other-item-id>",
		Short:   "Record that an item depends on another item",
		Long:    "The API rejects self-dependencies (422) and cycles (409).",
		Example: "  icb items add-dependency 018f... --depends-on 018e...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if dependsOn == "" {
				return usageError{fmt.Errorf("--depends-on is required")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			detail, err := client.AddDependency(cmd.Context(), args[0], api.DependencyInput{DependsOnID: dependsOn})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), detail)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Item %q now depends on %s (%d total dependencies)\n", detail.Title, dependsOn, len(detail.DependencyIDs))
			return nil
		},
	}
	cmd.Flags().StringVar(&dependsOn, "depends-on", "", "Item id this item depends on (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the item detail as JSON to stdout")
	return cmd
}

func newItemsRemoveDependencyCommand() *cobra.Command {
	var (
		dependsOn string
		yes       bool
	)
	cmd := &cobra.Command{
		Use:     "remove-dependency <item-id> --depends-on <other-item-id>",
		Short:   "Remove a dependency edge between two items",
		Example: "  icb items remove-dependency 018f... --depends-on 018e...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if dependsOn == "" {
				return usageError{fmt.Errorf("--depends-on is required")}
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Remove dependency %s → %s?", args[0], dependsOn))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if err := client.RemoveDependency(cmd.Context(), args[0], dependsOn); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Removed dependency %s → %s\n", args[0], dependsOn)
			return nil
		},
	}
	cmd.Flags().StringVar(&dependsOn, "depends-on", "", "Dependency item id to remove (required)")
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// --- Tasks (sub-verbs on an item) ---

func newItemsTasksCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "tasks <item-id>",
		Short:   "List an item's tasks",
		Example: "  icb items tasks 018f...",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			tasks, err := client.ListItemTasks(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), tasks)
			}
			printTasksTable(cmd.OutOrStdout(), tasks)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output tasks as JSON to stdout")
	return cmd
}

func newItemsAddTaskCommand() *cobra.Command {
	var (
		title    string
		position int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "add-task <item-id> --title <title>",
		Short:   "Add a task to an item",
		Example: "  icb items add-task 018f... --title \"write tests\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if title == "" {
				return usageError{fmt.Errorf("--title is required")}
			}
			in := api.ProjectItemTaskCreateInput{Title: title}
			if cmd.Flags().Changed("position") {
				in.Position = &position
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.CreateItemTask(cmd.Context(), args[0], in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Added task %q (%s)\n", task.Title, task.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "Task title (required)")
	cmd.Flags().IntVar(&position, "position", 0, "Task position within the item")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created task as JSON to stdout")
	return cmd
}

func newItemsCompleteTaskCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "complete-task <item-id> <task-id>",
		Short:   "Mark an item's task completed",
		Example: "  icb items complete-task 018f... 018g...",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			done := true
			return runTaskUpdate(cmd, args[0], args[1], api.ProjectItemTaskUpdateInput{Completed: &done}, asJSON)
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated task as JSON to stdout")
	return cmd
}

func newItemsEditTaskCommand() *cobra.Command {
	var (
		title     string
		completed bool
		position  int
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "edit-task <item-id> <task-id> [flags]",
		Short:   "Change a task's title, completion, or position",
		Example: "  icb items edit-task 018f... 018g... --title \"new\" --completed",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ProjectItemTaskUpdateInput{}
			if f.Changed("title") {
				in.Title = &title
			}
			if f.Changed("completed") {
				in.Completed = &completed
			}
			if f.Changed("position") {
				in.Position = &position
			}
			if in == (api.ProjectItemTaskUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass --title, --completed, and/or --position")}
			}
			return runTaskUpdate(cmd, args[0], args[1], in, asJSON)
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "New task title")
	cmd.Flags().BoolVar(&completed, "completed", false, "Set completion state")
	cmd.Flags().IntVar(&position, "position", 0, "New position")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated task as JSON to stdout")
	return cmd
}

// runTaskUpdate applies a PATCH to a task and renders it — shared by
// complete-task and edit-task.
func runTaskUpdate(cmd *cobra.Command, itemID, taskID string, in api.ProjectItemTaskUpdateInput, asJSON bool) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	task, err := client.UpdateItemTask(cmd.Context(), itemID, taskID, in)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), task)
	}
	fmt.Fprintf(cmd.OutOrStdout(), "Updated task %q → %s (%s)\n", task.Title, taskState(task), task.ID)
	return nil
}

func newItemsRemoveTaskCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "remove-task <item-id> <task-id>",
		Short:   "Delete a task from an item",
		Example: "  icb items remove-task 018f... 018g... --yes",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete task %s?", args[1]))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if err := client.DeleteItemTask(cmd.Context(), args[0], args[1]); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted task %s\n", args[1])
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// --- Rendering ---

func printItemsTable(out io.Writer, items []api.ProjectItem) {
	if len(items) == 0 {
		fmt.Fprintln(out, "No items.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "STATUS\tTITLE\tID")
	for _, it := range items {
		fmt.Fprintf(tw, "%s\t%s\t%s\n", flatItemStatus(it), it.Title, it.ID)
	}
	_ = tw.Flush()
}

func printItemDetail(out io.Writer, d api.ProjectItemDetail, tasks []api.ProjectItemTask, blockers []api.ProjectItem) {
	fmt.Fprintf(out, "%s\n", d.Title)
	fmt.Fprintf(out, "  id:      %s\n", d.ID)
	fmt.Fprintf(out, "  status:  %s\n", detailStatus(d))
	if n := strValue(d.Notes); n != "" {
		fmt.Fprintf(out, "  notes:   %s\n", n)
	}

	projectNames := make([]string, 0, len(d.Projects))
	for _, p := range d.Projects {
		projectNames = append(projectNames, p.Name)
	}
	fmt.Fprintf(out, "  projects: %s\n", orNone(strings.Join(projectNames, ", ")))
	fmt.Fprintf(out, "  depends on: %d item(s)\n", len(d.DependencyIDs))

	fmt.Fprintf(out, "\nTasks (%d):\n", len(tasks))
	if len(tasks) == 0 {
		fmt.Fprintln(out, "  (none)")
	} else {
		printTasksTable(out, tasks)
	}

	if len(blockers) > 0 {
		fmt.Fprintf(out, "\nBlocked by %d incomplete item(s):\n", len(blockers))
		printItemsTable(out, blockers)
	}
}

func printTasksTable(out io.Writer, tasks []api.ProjectItemTask) {
	if len(tasks) == 0 {
		fmt.Fprintln(out, "No tasks.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "  #\tSTATUS\tTITLE\tID")
	for _, t := range tasks {
		fmt.Fprintf(tw, "  %d\t%s\t%s\t%s\n", t.Position, taskState(t), t.Title, t.ID)
	}
	_ = tw.Flush()
}

func flatItemStatus(it api.ProjectItem) string {
	switch {
	case it.Archived:
		return "archived"
	case it.Completed:
		return "done"
	default:
		return "open"
	}
}

func detailStatus(d api.ProjectItemDetail) string {
	switch {
	case d.Archived:
		return "archived"
	case d.Completed:
		return "done"
	default:
		return "open"
	}
}

func taskState(t api.ProjectItemTask) string {
	if t.Completed {
		return "done"
	}
	return "open"
}

// orNone renders an empty string as "(none)" for list-style detail fields.
func orNone(s string) string {
	if s == "" {
		return "(none)"
	}
	return s
}
