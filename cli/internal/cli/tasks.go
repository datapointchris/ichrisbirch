package cli

import (
	"fmt"
	"io"
	"strconv"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newTasksCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tasks",
		Short: "List, inspect, and manage your tasks",
		Long: "Work with the standalone Tasks app — the flat, priority-ranked maintenance\n" +
			"list (distinct from project items). Requires a logged-in session\n" +
			"(`icb auth login`).",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newTasksListCommand(),
		newTasksTodoCommand(),
		newTasksCompletedCommand(),
		newTasksSearchCommand(),
		newTasksViewCommand(),
		newTasksCreateCommand(),
		newTasksEditCommand(),
		newTasksCompleteCommand(),
		newTasksShiftCommand(),
		newTasksReorderCommand(),
		newTasksDeleteCommand(),
	)
	return cmd
}

func newTasksListCommand() *cobra.Command {
	var (
		limit  int
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List all tasks by priority",
		Example: "  icb tasks list\n  icb tasks list --limit 10 --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runTaskList(cmd, asJSON, func(c *api.Client) ([]api.Task, error) {
				return c.ListTasks(cmd.Context(), limitFlag(cmd))
			})
		},
	}
	cmd.Flags().IntVar(&limit, "limit", 0, "Maximum number of tasks to return")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output tasks as JSON to stdout")
	return cmd
}

func newTasksTodoCommand() *cobra.Command {
	var (
		limit  int
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "todo",
		Short:   "List incomplete tasks by priority",
		Example: "  icb tasks todo\n  icb tasks todo --limit 5",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runTaskList(cmd, asJSON, func(c *api.Client) ([]api.Task, error) {
				return c.ListTodoTasks(cmd.Context(), limitFlag(cmd))
			})
		},
	}
	cmd.Flags().IntVar(&limit, "limit", 0, "Maximum number of tasks to return")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output tasks as JSON to stdout")
	return cmd
}

func newTasksCompletedCommand() *cobra.Command {
	var (
		start  string
		end    string
		first  bool
		last   bool
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "completed",
		Short:   "List completed tasks",
		Long:    "List completed tasks. With no flags, all are returned; --first/--last give\nthe single earliest/most-recent; --start/--end bound a date range (ISO 8601).",
		Example: "  icb tasks completed --last\n  icb tasks completed --start 2026-01-01 --end 2026-07-01",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			q := api.CompletedTasksQuery{StartDate: start, EndDate: end, First: first, Last: last}
			return runTaskList(cmd, asJSON, func(c *api.Client) ([]api.Task, error) {
				return c.ListCompletedTasks(cmd.Context(), q)
			})
		},
	}
	cmd.Flags().StringVar(&start, "start", "", "Range start (ISO 8601, e.g. 2026-01-01)")
	cmd.Flags().StringVar(&end, "end", "", "Range end (ISO 8601)")
	cmd.Flags().BoolVar(&first, "first", false, "Only the earliest completed task")
	cmd.Flags().BoolVar(&last, "last", false, "Only the most recently completed task")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output tasks as JSON to stdout")
	return cmd
}

func newTasksSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search tasks by name or notes",
		Example: "  icb tasks search invoice",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runTaskList(cmd, asJSON, func(c *api.Client) ([]api.Task, error) {
				return c.SearchTasks(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output tasks as JSON to stdout")
	return cmd
}

func newTasksViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <task-id>",
		Short:   "Show a single task",
		Example: "  icb tasks view 42",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("task id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.GetTask(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			printTaskDetail(cmd.OutOrStdout(), task)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the task as JSON to stdout")
	return cmd
}

func newTasksCreateCommand() *cobra.Command {
	var (
		name     string
		notes    string
		category string
		priority int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "create --name <name> --category <category> [flags]",
		Short:   "Create a new task",
		Example: "  icb tasks create --name \"Renew registration\" --category chore --priority 3",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return usageError{fmt.Errorf("--name is required")}
			}
			if category == "" {
				return usageError{fmt.Errorf("--category is required")}
			}
			in := api.TaskCreateInput{Name: name, Category: category}
			if cmd.Flags().Changed("notes") {
				in.Notes = &notes
			}
			if cmd.Flags().Changed("priority") {
				in.Priority = &priority
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.CreateTask(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Created task %q (id %d, priority %d)\n", task.Name, task.ID, task.Priority)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Task name (required)")
	cmd.Flags().StringVar(&notes, "notes", "", "Markdown notes")
	cmd.Flags().StringVar(&category, "category", "", "Task category (required)")
	cmd.Flags().IntVar(&priority, "priority", 1, "Priority rank (lower = higher priority)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created task as JSON to stdout")
	return cmd
}

func newTasksEditCommand() *cobra.Command {
	var (
		name     string
		notes    string
		category string
		priority int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "edit <task-id> [flags]",
		Short:   "Change fields on an existing task",
		Long:    "Update only the fields whose flags you pass. Use `complete` to finish a task.",
		Example: "  icb tasks edit 42 --priority 1 --notes \"due friday\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("task id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.TaskUpdateInput{}
			if f.Changed("name") {
				in.Name = &name
			}
			if f.Changed("notes") {
				in.Notes = &notes
			}
			if f.Changed("category") {
				in.Category = &category
			}
			if f.Changed("priority") {
				in.Priority = &priority
			}
			if in == (api.TaskUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass at least one of --name/--notes/--category/--priority")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.UpdateTask(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Updated task %q (id %d)\n", task.Name, task.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New task name")
	cmd.Flags().StringVar(&notes, "notes", "", "New markdown notes")
	cmd.Flags().StringVar(&category, "category", "", "New category")
	cmd.Flags().IntVar(&priority, "priority", 1, "New priority rank")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated task as JSON to stdout")
	return cmd
}

func newTasksCompleteCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "complete <task-id>",
		Short:   "Mark a task completed",
		Example: "  icb tasks complete 42",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("task id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.CompleteTask(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Completed task %q (id %d)\n", task.Name, task.ID)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the task as JSON to stdout")
	return cmd
}

func newTasksShiftCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "shift <task-id> <positions>",
		Short:   "Shift a task's priority rank",
		Long:    "Move a task by <positions> ranks: positive pushes it down the list (lower\npriority), negative pulls it up. Nightly compaction absorbs any gaps.",
		Example: "  icb tasks shift 42 -2   # up two\n  icb tasks shift 42 3    # down three",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("task id", args[0])
			if err != nil {
				return err
			}
			positions, err := parseIntArg("positions", args[1])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.ShiftTask(cmd.Context(), id, positions)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Shifted task %q to priority %d (id %d)\n", task.Name, task.Priority, task.ID)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the task as JSON to stdout")
	return cmd
}

func newTasksReorderCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "reorder",
		Short:   "Dense-rank incomplete task priorities to 1..K",
		Long:    "Tidy the priority ranks of all incomplete tasks to a gap-free 1..K sequence — the same operation the nightly scheduler runs.",
		Example: "  icb tasks reorder",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			message, err := client.ReorderTasks(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintln(cmd.OutOrStdout(), message)
			return nil
		},
	}
	return cmd
}

func newTasksDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <task-id>",
		Short:   "Delete a task",
		Example: "  icb tasks delete 42 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("task id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.GetTask(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete task %q (id %d)? This cannot be undone.", task.Name, task.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteTask(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted task %q (id %d)\n", task.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// runTaskList runs a fetch returning []Task and renders it as JSON or a table —
// the shared body of list/todo/completed/search.
func runTaskList(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.Task, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	tasks, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), tasks)
	}
	printTaskList(cmd.OutOrStdout(), tasks)
	return nil
}

// limitFlag returns a *int for the --limit flag, or nil when it was not set (so
// the client omits the query param and the API returns everything).
func limitFlag(cmd *cobra.Command) *int {
	if !cmd.Flags().Changed("limit") {
		return nil
	}
	v, _ := cmd.Flags().GetInt("limit")
	return &v
}

// parseIntArg converts a positional argument to an int, classifying a bad value
// as a usage error (exit 2).
func parseIntArg(name, s string) (int, error) {
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0, usageError{fmt.Errorf("invalid %s %q: must be an integer", name, s)}
	}
	return n, nil
}

func printTaskList(out io.Writer, tasks []api.Task) {
	if len(tasks) == 0 {
		fmt.Fprintln(out, "No tasks.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tPRI\tSTATUS\tCATEGORY\tNAME")
	for _, t := range tasks {
		fmt.Fprintf(tw, "%d\t%d\t%s\t%s\t%s\n", t.ID, t.Priority, taskStatus(t), t.Category, t.Name)
	}
	_ = tw.Flush()
}

func printTaskDetail(out io.Writer, t api.Task) {
	fmt.Fprintf(out, "%s\n", t.Name)
	fmt.Fprintf(out, "  id:        %d\n", t.ID)
	fmt.Fprintf(out, "  category:  %s\n", t.Category)
	fmt.Fprintf(out, "  priority:  %d\n", t.Priority)
	fmt.Fprintf(out, "  status:    %s\n", taskStatus(t))
	fmt.Fprintf(out, "  added:     %s\n", t.AddDate.Format("2006-01-02"))
	if t.CompleteDate != nil {
		fmt.Fprintf(out, "  completed: %s\n", t.CompleteDate.Format("2006-01-02"))
	}
	if n := strValue(t.Notes); n != "" {
		fmt.Fprintf(out, "  notes:     %s\n", n)
	}
}

func taskStatus(t api.Task) string {
	if t.Completed() {
		return "done"
	}
	return "open"
}
