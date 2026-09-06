package cli

import (
	"errors"
	"fmt"
	"io"
	"slices"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/prompt"
)

func newTasksCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tasks",
		Short: "List, inspect, and manage your tasks",
		Long: "The flat, priority-ranked maintenance list — chores and one-offs that belong\n" +
			"to no project. Structured work lives in `icb projects items` instead.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd,
		"Search tasks by name or notes: icb tasks search <query>",
		"Completed tasks are hidden: icb tasks list --status all",
	)
	cmd.AddCommand(
		newTasksListCommand(),
		newTasksSearchCommand(),
		newTasksShowCommand(),
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
		limit      int
		asJSON     bool
		taskStatus string
		category   string
		bounds     api.DateBounds
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List open tasks by priority",
		Long: "Open is the default because completed tasks accumulate without bound.\n" +
			"\n" +
			"--status takes one of: " + strings.Join(api.TaskStatuses, ", ") + ". Completed tasks come\n" +
			"back most-recently-finished first — priority stopped meaning anything the\n" +
			"moment they left the queue.\n" +
			"\n" +
			"--start/--end bound when a task was completed, inclusive on both ends, and\n" +
			"either works without the other. An open task has no completion date, so it\n" +
			"falls outside every range — pair them with --status completed to read a\n" +
			"week's finished work.\n" +
			"\n" +
			"--category narrows to one of: " + strings.Join(api.TaskCategories, ", ") + ".\n" +
			"It is matched by the API, so --limit caps the category rather than the\n" +
			"whole list.",
		Example: "  icb tasks list\n" +
			"  icb tasks list --category Personal\n" +
			"  icb tasks list --status completed\n" +
			"  icb tasks list --status completed --start 2026-08-17 --end 2026-08-23\n" +
			"  icb tasks list --status all --limit 10 --json",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if cmd.Flags().Changed("status") && !slices.Contains(api.TaskStatuses, taskStatus) {
				return usageError{fmt.Errorf("unknown status %q — one of: %s", taskStatus, strings.Join(api.TaskStatuses, ", "))}
			}
			if cmd.Flags().Changed("category") {
				// The same validator `create` and `edit` use, so a category one door
				// accepts is accepted by all three and the spelling is corrected once.
				canonical, err := taskCategory(category)
				if err != nil {
					return usageError{err}
				}
				category = canonical
			}
			if err := runTaskList(cmd, asJSON, func(c *api.Client) ([]api.Task, error) {
				return c.ListTasks(cmd.Context(), limitFlag(cmd), taskStatus, category, bounds)
			}); err != nil {
				return err
			}
			if !asJSON && !cmd.Flags().Changed("status") {
				_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nCompleted tasks are hidden: icb tasks list --status all")
			}
			return nil
		},
	}
	addLimitFlag(cmd, &limit)
	cmd.Flags().StringVar(&taskStatus, "status", "", "One of: "+strings.Join(api.TaskStatuses, ", ")+" (default open)")
	cmd.Flags().StringVar(&category, "category", "", "Only tasks in this category: "+strings.Join(api.TaskCategories, ", "))
	cmd.Flags().StringVar(&bounds.Start, "start", "", "Only tasks completed on or after this ISO 8601 date")
	cmd.Flags().StringVar(&bounds.End, "end", "", "Only tasks completed on or before this ISO 8601 date")
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

func newTasksShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <task-id>",
		Short:   "Show a single task",
		Example: "  icb tasks show 42",
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

// taskCategory validates a category against the lookup table and returns it
// spelled the way the table spells it. One validator serves the flag and the
// prompt, so a category neither door accepts is refused the same way through
// both — with the list of what would have worked.
var taskCategory = prompt.OneOf(api.TaskCategories)

// taskCreateFields is the record `tasks create` builds, in the order it asks.
// The same list drives both doors: unanswered fields become the form, and the
// flags are checked against these validators before anything is sent.
func taskCreateFields() []prompt.Field {
	return []prompt.Field{
		{Key: "name", Label: "Name"},
		{
			Key:      "category",
			Label:    "Category",
			Choices:  api.TaskCategories,
			Validate: taskCategory,
		},
		{
			Key:      "priority",
			Label:    "Priority",
			Hint:     "Priority is a rank — lower comes first.",
			Default:  "1",
			Validate: prompt.Int,
		},
		{Key: "notes", Label: "Notes", Optional: true},
	}
}

func newTasksCreateCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "create [flags]",
		Short: "Create a new task",
		Long: "Pass every field as a flag to create in one shot. Leave --name or\n" +
			"--category out at a terminal and the rest are asked for one at a time,\n" +
			"with the categories listed and Tab cycling them. A flag already passed\n" +
			"is never asked about.\n" +
			"\n" +
			"An answer the field rejects comes back for editing and nothing already\n" +
			"entered is lost. Ctrl-C abandons the task.",
		Example: "  icb tasks create\n" +
			"  icb tasks create --name \"Renew registration\" --category chore --priority 3",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			fields := taskCreateFields()
			answers := flagAnswers(cmd, "name", "category", "priority", "notes")
			if err := validateAnswers(answers, fields); err != nil {
				return usageError{err}
			}
			if missing := missingFlags(answers, "name", "category"); len(missing) > 0 {
				if !interactive(cmd) {
					return usageError{fmt.Errorf("%s required — pass them, or run from a terminal to be asked",
						strings.Join(missing, " and "))}
				}
				asked, err := runForm(cmd, prompt.Form{
					Intro:  "Creating a task. Ctrl-C to abandon it.",
					Fields: unanswered(fields, answers),
				})
				if errors.Is(err, errAborted) {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nAborted.")
					return nil
				}
				if err != nil {
					return err
				}
				answers.Merge(asked)
			}
			in := api.TaskCreateInput{Name: answers.Get("name"), Category: answers.Get("category")}
			if answers.Has("notes") {
				notes := answers.Get("notes")
				in.Notes = &notes
			}
			if answers.Has("priority") {
				// Unfailable: pflag parses the flag as an int and prompt.Int
				// parses the typed answer, so nothing unparsed reaches here.
				priority, _ := strconv.Atoi(answers.Get("priority"))
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
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created task %q (id %d, priority %d)\n", task.Name, task.ID, task.Priority)
			return nil
		},
	}
	cmd.Flags().String("name", "", "Task name (asked for when omitted)")
	cmd.Flags().String("notes", "", "Markdown notes")
	cmd.Flags().String("category", "", "One of: "+strings.Join(api.TaskCategories, ", ")+" (asked for when omitted)")
	cmd.Flags().Int("priority", 1, "Priority rank (lower = higher priority)")
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
				canonical, err := taskCategory(category)
				if err != nil {
					return usageError{fmt.Errorf("--category: %w", err)}
				}
				in.Category = &canonical
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
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated task %q (id %d)\n", task.Name, task.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New task name")
	cmd.Flags().StringVar(&notes, "notes", "", "New markdown notes")
	cmd.Flags().StringVar(&category, "category", "", "New category, one of: "+strings.Join(api.TaskCategories, ", "))
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
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Completed task %q (id %d)\n", task.Name, task.ID)
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
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Shifted task %q to priority %d (id %d)\n", task.Name, task.Priority, task.ID)
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
			_, _ = fmt.Fprintln(cmd.OutOrStdout(), message)
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
				ok, err := confirm(cmd,
					fmt.Sprintf("Delete task %q (id %d)? This cannot be undone.", task.Name, task.ID))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteTask(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted task %q (id %d)\n", task.Name, id)
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
		_, _ = fmt.Fprintln(out, "No tasks.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tPRI\tSTATUS\tCATEGORY\tNAME")
	for _, t := range tasks {
		_, _ = fmt.Fprintf(tw, "%d\t%d\t%s\t%s\t%s\n", t.ID, t.Priority, taskStatus(t), t.Category, t.Name)
	}
	_ = tw.Flush()
}

func printTaskDetail(out io.Writer, t api.Task) {
	_, _ = fmt.Fprintf(out, "%s\n", t.Name)
	_, _ = fmt.Fprintf(out, "  id:        %d\n", t.ID)
	_, _ = fmt.Fprintf(out, "  category:  %s\n", t.Category)
	_, _ = fmt.Fprintf(out, "  priority:  %d\n", t.Priority)
	_, _ = fmt.Fprintf(out, "  status:    %s\n", taskStatus(t))
	_, _ = fmt.Fprintf(out, "  added:     %s\n", t.AddDate.Format("2006-01-02"))
	if t.CompleteDate != nil {
		_, _ = fmt.Fprintf(out, "  completed: %s\n", t.CompleteDate.Format("2006-01-02"))
	}
	if n := strValue(t.Notes); n != "" {
		_, _ = fmt.Fprintf(out, "  notes:     %s\n", n)
	}
}

func taskStatus(t api.Task) string { return itemStatusWord(false, t.Completed()) }
