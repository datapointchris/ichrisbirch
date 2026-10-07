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
		Long: "The flat maintenance list — chores and one-offs that belong to no project.\n" +
			"Structured work lives in `icb projects items` instead.\n" +
			"\n" +
			"Each task has a window in days, its category's unless one is given. A task\n" +
			"climbs the list as its window runs out, so a short window comes up sooner\n" +
			"than a long one added earlier. The order is the whole signal: no date is\n" +
			"shown. `snooze` restarts a task's window, `pin` holds it at the top, and\n" +
			"`drop` lets it go while keeping it on record.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd,
		"Search tasks by name or notes: icb tasks search <query>",
		"Completed and dropped tasks are hidden: icb tasks list --status all",
	)
	cmd.AddCommand(
		newTasksListCommand(),
		newTasksSearchCommand(),
		newTasksShowCommand(),
		newTasksCreateCommand(),
		newTasksEditCommand(),
		newTasksCompleteCommand(),
		newTasksSnoozeCommand(),
		newTasksPinCommand(true),
		newTasksPinCommand(false),
		newTasksDropCommand(),
		newTasksDeleteCommand(),
		newTaskCategoriesCommand(),
	)
	return cmd
}

func newTasksListCommand() *cobra.Command {
	var (
		limit      int
		asJSON     bool
		taskStatus string
		category   string
		start      string
		end        string
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List open tasks in the order to do them",
		Long: "Open is the default because closed tasks accumulate without bound. Open\n" +
			"tasks come back pinned first, then in the order their windows run out.\n" +
			"\n" +
			"--status takes one of: " + strings.Join(api.TaskStatuses, ", ") + ". Completed and\n" +
			"dropped tasks come back most-recently-closed first — a place in the queue\n" +
			"stops meaning anything once a task leaves it.\n" +
			"\n" +
			"--start/--end bound when a task was closed, inclusive on both ends, and\n" +
			"either works without the other: the drop date for --status dropped, the\n" +
			"completion date otherwise. A bound with no offset is taken in this machine's\n" +
			"zone. An open task has no closing date, so it falls outside every range —\n" +
			"pair them with --status completed to read a week's finished work.\n" +
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
				return c.ListTasks(cmd.Context(), limitFlag(cmd), taskStatus, category,
					api.OnOrAfter(start), api.OnOrBefore(end), api.DayZone(LocalZoneName()))
			}); err != nil {
				return err
			}
			if !asJSON && !cmd.Flags().Changed("status") {
				_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nCompleted and dropped tasks are hidden: icb tasks list --status all")
			}
			return nil
		},
	}
	addLimitFlag(cmd, &limit)
	cmd.Flags().StringVar(&taskStatus, "status", "", "One of: "+strings.Join(api.TaskStatuses, ", ")+" (default open)")
	cmd.Flags().StringVar(&category, "category", "", "Only tasks in this category: "+strings.Join(api.TaskCategories, ", "))
	cmd.Flags().StringVar(&start, "start", "", "Only tasks closed on or after this ISO 8601 date")
	cmd.Flags().StringVar(&end, "end", "", "Only tasks closed on or before this ISO 8601 date")
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
			Key:      "window-days",
			Label:    "Window in days",
			Hint:     "How soon it should come up. Blank takes the category's window.",
			Optional: true,
			Validate: windowDays,
		},
		{Key: "notes", Label: "Notes", Optional: true},
	}
}

// windowDays is the floor the API holds a window to, so a zero is refused
// here with the reason rather than coming back as a 422.
var windowDays = prompt.IntAtLeast(1)

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
			"  icb tasks create --name \"Renew registration\" --category chore --window-days 14",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			fields := taskCreateFields()
			answers := flagAnswers(cmd, "name", "category", "window-days", "notes")
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
			if answers.Has("window-days") {
				// Unfailable: validateAnswers and the form both ran windowDays,
				// so nothing unparsed reaches here.
				window, _ := strconv.Atoi(answers.Get("window-days"))
				in.WindowDays = &window
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
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created task %q (id %d, %d-day window)\n", task.Name, task.ID, task.WindowDays)
			return nil
		},
	}
	cmd.Flags().String("name", "", "Task name (asked for when omitted)")
	cmd.Flags().String("notes", "", "Markdown notes")
	cmd.Flags().String("category", "", "One of: "+strings.Join(api.TaskCategories, ", ")+" (asked for when omitted)")
	cmd.Flags().Int("window-days", 0, "Days before it comes up (default the category's window)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created task as JSON to stdout")
	return cmd
}

func newTasksEditCommand() *cobra.Command {
	var (
		name     string
		notes    string
		category string
		window   int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:   "edit <task-id> [flags]",
		Short: "Change fields on an existing task",
		Long: "Update only the fields whose flags you pass. A new --window-days applies\n" +
			"from the next snooze; `snooze` restarts the window now. Use `complete` to\n" +
			"finish a task and `drop` to let one go.",
		Example: "  icb tasks edit 42 --window-days 7 --notes \"due friday\"",
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
			if f.Changed("window-days") {
				if _, err := windowDays(strconv.Itoa(window)); err != nil {
					return usageError{fmt.Errorf("--window-days: %w", err)}
				}
				in.WindowDays = &window
			}
			if in == (api.TaskUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass at least one of --name/--notes/--category/--window-days")}
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
	cmd.Flags().IntVar(&window, "window-days", 0, "New window in days, at least 1")
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

// taskActionCommand is the shape snooze, pin, unpin and drop share: one task id,
// one call, and a one-line confirmation or the task as JSON.
func taskActionCommand(use, short, long, example, done string, act func(*cobra.Command, *api.Client, int) (api.Task, error)) *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     use,
		Short:   short,
		Long:    long,
		Example: example,
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
			task, err := act(cmd, client, id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s task %q (id %d)\n", done, task.Name, task.ID)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the task as JSON to stdout")
	return cmd
}

func newTasksSnoozeCommand() *cobra.Command {
	return taskActionCommand(
		"snooze <task-id>",
		"Restart a task's window, moving it back down the list",
		"Not now: the task's window starts again from today, so it comes back up\n"+
			"after as many days as its window holds. A pinned task is unpinned.",
		"  icb tasks snooze 42",
		"Snoozed",
		func(cmd *cobra.Command, c *api.Client, id int) (api.Task, error) {
			return c.SnoozeTask(cmd.Context(), id)
		},
	)
}

func newTasksPinCommand(pinned bool) *cobra.Command {
	if pinned {
		return taskActionCommand(
			"pin <task-id>",
			"Hold a task at the top of the list",
			"A pinned task sorts ahead of every unpinned one until it is unpinned,\n"+
				"snoozed, or closed.",
			"  icb tasks pin 42",
			"Pinned",
			func(cmd *cobra.Command, c *api.Client, id int) (api.Task, error) {
				return c.SetTaskPinned(cmd.Context(), id, true)
			},
		)
	}
	return taskActionCommand(
		"unpin <task-id>",
		"Return a pinned task to its place by window",
		"",
		"  icb tasks unpin 42",
		"Unpinned",
		func(cmd *cobra.Command, c *api.Client, id int) (api.Task, error) {
			return c.SetTaskPinned(cmd.Context(), id, false)
		},
	)
}

func newTasksDropCommand() *cobra.Command {
	var reason string
	cmd := taskActionCommand(
		"drop <task-id> [--reason <why>]",
		"Let a task go without completing it",
		"A dropped task leaves the list and stays on record under --status dropped.\n"+
			"It does not count as completed. --reason is optional and kept with it.",
		"  icb tasks drop 42 --reason \"bought one instead\"",
		"Dropped",
		func(cmd *cobra.Command, c *api.Client, id int) (api.Task, error) {
			return c.DropTask(cmd.Context(), id, reason)
		},
	)
	cmd.Flags().StringVar(&reason, "reason", "", "Why it is dropped")
	return cmd
}

func newTaskCategoriesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "categories",
		Short: "List and tune the categories --category accepts, with each one's window",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(newTaskCategoriesListCommand(), newTaskCategoriesEditCommand())
	return cmd
}

func newTaskCategoriesListCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List the task categories and the window a new task in each gets",
		Example: "  icb tasks categories list",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			categories, err := client.ListTaskCategories(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), categories)
			}
			tw := tabwriter.NewWriter(cmd.OutOrStdout(), 0, 4, 2, ' ', 0)
			_, _ = fmt.Fprintln(tw, "CATEGORY\tWINDOW (DAYS)")
			for _, c := range categories {
				_, _ = fmt.Fprintf(tw, "%s\t%d\n", c.Name, c.WindowDays)
			}
			return tw.Flush()
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the categories as JSON to stdout")
	return cmd
}

func newTaskCategoriesEditCommand() *cobra.Command {
	var (
		window int
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "edit <category> --window-days <days>",
		Short: "Change the window a new task in a category gets",
		Long: "Applies to tasks created afterwards. Open tasks keep the window they were\n" +
			"made with.",
		Example: "  icb tasks categories edit Home --window-days 45",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			name, err := taskCategory(args[0])
			if err != nil {
				return usageError{err}
			}
			if !cmd.Flags().Changed("window-days") {
				return usageError{errors.New("--window-days is required")}
			}
			if _, err := windowDays(strconv.Itoa(window)); err != nil {
				return usageError{fmt.Errorf("--window-days: %w", err)}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			category, err := client.UpdateTaskCategory(cmd.Context(), name, window)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), category)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s tasks now get a %d-day window\n", category.Name, category.WindowDays)
			return nil
		},
	}
	cmd.Flags().IntVar(&window, "window-days", 0, "Window in days, at least 1")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the category as JSON to stdout")
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
	// The row number is the queue position. The sort date behind it is never
	// printed, so the list reads as an order rather than a set of deadlines.
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "#\tID\tPIN\tSTATUS\tCATEGORY\tNAME")
	for i, t := range tasks {
		_, _ = fmt.Fprintf(tw, "%d\t%d\t%s\t%s\t%s\t%s\n", i+1, t.ID, pinMark(t), taskStatus(t), t.Category, t.Name)
	}
	_ = tw.Flush()
}

func pinMark(t api.Task) string {
	if t.Pinned {
		return "pin"
	}
	return ""
}

func printTaskDetail(out io.Writer, t api.Task) {
	_, _ = fmt.Fprintf(out, "%s\n", t.Name)
	_, _ = fmt.Fprintf(out, "  id:        %d\n", t.ID)
	_, _ = fmt.Fprintf(out, "  category:  %s\n", t.Category)
	_, _ = fmt.Fprintf(out, "  window:    %d days\n", t.WindowDays)
	if t.Pinned {
		_, _ = fmt.Fprintln(out, "  pinned:    yes")
	}
	_, _ = fmt.Fprintf(out, "  status:    %s\n", taskStatus(t))
	if t.AutoTaskID != nil {
		_, _ = fmt.Fprintf(out, "  autotask:  %d\n", *t.AutoTaskID)
	}
	_, _ = fmt.Fprintf(out, "  added:     %s\n", localDay(t.AddDate))
	if t.CompleteDate != nil {
		_, _ = fmt.Fprintf(out, "  completed: %s\n", localDay(*t.CompleteDate))
	}
	if t.DropDate != nil {
		_, _ = fmt.Fprintf(out, "  dropped:   %s\n", localDay(*t.DropDate))
	}
	if r := strValue(t.DropReason); r != "" {
		_, _ = fmt.Fprintf(out, "  reason:    %s\n", r)
	}
	if n := strValue(t.Notes); n != "" {
		_, _ = fmt.Fprintf(out, "  notes:     %s\n", n)
	}
}

func taskStatus(t api.Task) string {
	switch {
	case t.Dropped():
		return api.TaskStatusDropped
	case t.Completed():
		return api.TaskStatusCompleted
	default:
		return api.TaskStatusOpen
	}
}
