package cli

import (
	"cmp"
	"errors"
	"fmt"
	"io"
	"math"
	"slices"
	"strconv"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// habitHints and habitAndCategoryHints are the commands that find a valid id
// for the two things a habits verb takes.
var (
	habitHints = []string{"List every habit: icb habits list"}

	habitAndCategoryHints = append(slices.Clone(habitHints),
		"List the categories a habit can belong to: icb habits categories")
)

func newHabitsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "habits",
		Short: "List, inspect, complete, and manage your habits",
		Long:  "The things you are trying to do every day, grouped into categories, with a\ncompletion recorded each time you do one.",
		RunE:  requireSubcommand,
	}
	withNotFoundHints(cmd, habitHints...)
	cmd.AddCommand(
		newHabitsTodayCommand(),
		newHabitsListCommand(),
		newHabitsShowCommand(),
		// create and edit take a category id as well as a habit id, so a 404
		// under either can be about a category the group's hints never mention.
		withNotFoundHints(newHabitsCreateCommand(), habitAndCategoryHints...),
		withNotFoundHints(newHabitsEditCommand(), habitAndCategoryHints...),
		newHabitsDeleteCommand(),
		newHabitsCompleteCommand(),
		newHabitsCategoriesCommand(),
		newHabitsCompletedCommand(),
	)
	return cmd
}

// newHabitsTodayCommand is the board you read each morning. It takes no --limit:
// the set is every habit you are currently tracking, so a cap can only hide one
// you still owe. `icb overview` is the capped view.
func newHabitsTodayCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "today",
		Short: "Show today's habits — which are done and which are still due",
		Long: "Every habit you are currently tracking, marked done or still due, ordered by\n" +
			"id. The whole set, never an excerpt.\n\n" +
			"The server composes the board and names the day. This sends the machine's IANA\n" +
			"timezone, so the day ends where you are rather than at UTC midnight, and the\n" +
			"header names the zone it was read in. A machine whose zone cannot be read falls\n" +
			"back to UTC, which the header then says.",
		Example: "  icb habits today\n  icb habits today --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			board, err := client.GetHabitsDay(cmd.Context(), "", LocalZoneName())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), board)
			}
			printHabitsDay(cmd.OutOrStdout(), board)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the day's habits as JSON to stdout")
	return cmd
}

// habitTodayRow is one line of the board. ID is the habit's, and is zero for a
// completion that carries no habit_id — a legacy row, or one whose habit has been
// deleted. That is the only row the board cannot hand a handle back for.
type habitTodayRow struct {
	ID       int
	Category string
	Name     string
	Done     bool
}

// habitsDayRows interleaves the due and done halves into one board. The server
// sends both in habit-id order, and merging them on that id is what keeps a
// finished habit in its row rather than moving it to a trailing block.
func habitsDayRows(board api.HabitsDay) []habitTodayRow {
	rows := make([]habitTodayRow, 0, len(board.Due)+len(board.Completed))
	for _, habit := range board.Due {
		rows = append(rows, habitTodayRow{ID: habit.ID, Category: habit.Category.Name, Name: habit.Name})
	}
	for _, completion := range board.Completed {
		row := habitTodayRow{Category: completion.Category.Name, Name: completion.Name, Done: true}
		if completion.HabitID != nil {
			row.ID = *completion.HabitID
		}
		rows = append(rows, row)
	}
	slices.SortStableFunc(rows, func(a, b habitTodayRow) int {
		return cmp.Compare(habitPlacementID(a.ID), habitPlacementID(b.ID))
	})
	return rows
}

// habitPlacementID is the sort key for a board row. Zero means the row records a
// completion carrying no habit_id, so there is no id to place it by and it sorts
// after every row that has one.
func habitPlacementID(habitID int) int {
	if habitID == 0 {
		return math.MaxInt
	}
	return habitID
}

// printHabitsDay renders the board. The header names the zone the day was read
// in, because the zone decides which completions land on it. A machine that
// could not name its own zone reads as UTC there rather than going unmentioned.
func printHabitsDay(out io.Writer, board api.HabitsDay) {
	_, _ = fmt.Fprintf(out, "Habits (%d of %d done today, %s)\n", len(board.Completed), board.CurrentTotal, board.Timezone)
	rows := habitsDayRows(board)
	if len(rows) == 0 {
		_, _ = fmt.Fprintln(out, "No current habits. Start one with `icb habits create --name ... --category ...`.")
		return
	}
	_, _ = fmt.Fprintln(out)
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tNAME\tDONE\tCATEGORY")
	for _, row := range rows {
		id := ""
		if row.ID != 0 {
			id = strconv.Itoa(row.ID)
		}
		_, _ = fmt.Fprintf(tw, "%s\t%s\t%s\t%s\n", id, row.Name, yesNo(row.Done), row.Category)
	}
	_ = tw.Flush()
	if len(board.Due) > 0 {
		_, _ = fmt.Fprintln(out, "\nComplete one with `icb habits complete <id>`.")
	}
}

func newHabitsListCommand() *cobra.Command {
	var (
		current bool
		limit   int
		asJSON  bool
	)
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List habits",
		Example: "  icb habits list\n  icb habits list --current",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			habits, err := client.ListHabits(cmd.Context(), boolFlagPtr(cmd, "current"), limitFlag(cmd))
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), habits)
			}
			printHabitsTable(cmd.OutOrStdout(), habits)
			return nil
		},
	}
	cmd.Flags().BoolVar(&current, "current", false, "Filter by current status (--current or --current=false)")
	addLimitFlag(cmd, &limit)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output habits as JSON to stdout")
	return cmd
}

func newHabitsShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <habit-id>",
		Short:   "Show a single habit",
		Example: "  icb habits show 5",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("habit id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			habit, err := client.GetHabit(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), habit)
			}
			printHabitDetail(cmd.OutOrStdout(), habit)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the habit as JSON to stdout")
	return cmd
}

func newHabitsCreateCommand() *cobra.Command {
	var (
		name      string
		category  int
		isCurrent bool
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "create --name <name> --category <category-id> [flags]",
		Short:   "Create a new habit",
		Example: "  icb habits create --name \"Stretch\" --category 2",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return usageError{fmt.Errorf("--name is required")}
			}
			if !cmd.Flags().Changed("category") {
				return usageError{fmt.Errorf("--category (category id) is required")}
			}
			in := api.HabitCreateInput{Name: name, CategoryID: category}
			if cmd.Flags().Changed("is-current") {
				in.IsCurrent = &isCurrent
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			habit, err := client.CreateHabit(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), habit)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created habit %q (id %d)\n", habit.Name, habit.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Habit name (required)")
	cmd.Flags().IntVar(&category, "category", 0, "Category id (required) — icb habits categories prints them")
	cmd.Flags().BoolVar(&isCurrent, "is-current", true, "Whether the habit is currently tracked")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created habit as JSON to stdout")
	return cmd
}

func newHabitsEditCommand() *cobra.Command {
	var (
		name      string
		category  int
		isCurrent bool
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "edit <habit-id> [flags]",
		Short:   "Change fields on an existing habit",
		Long:    "Update only the fields whose flags you pass.",
		Example: "  icb habits edit 5 --is-current=false",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("habit id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.HabitUpdateInput{}
			if f.Changed("name") {
				in.Name = &name
			}
			if f.Changed("category") {
				in.CategoryID = &category
			}
			if f.Changed("is-current") {
				in.IsCurrent = &isCurrent
			}
			if in == (api.HabitUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass at least one of --name/--category/--is-current")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			habit, err := client.UpdateHabit(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), habit)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated habit %q (id %d)\n", habit.Name, habit.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New habit name")
	cmd.Flags().IntVar(&category, "category", 0, "New category id — icb habits categories prints them")
	cmd.Flags().BoolVar(&isCurrent, "is-current", true, "Set current-tracking status")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated habit as JSON to stdout")
	return cmd
}

func newHabitsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <habit-id>",
		Short:   "Delete a habit",
		Example: "  icb habits delete 5 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("habit id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			habit, err := client.GetHabit(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd,
					fmt.Sprintf("Delete habit %q (id %d)?", habit.Name, habit.ID))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteHabit(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted habit %q (id %d)\n", habit.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func newHabitsCompleteCommand() *cobra.Command {
	var (
		date   string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "complete <habit-id> [--date YYYY-MM-DD]",
		Short: "Record a completion of a habit",
		Long: "Mark a habit done, by default today on this machine's calendar. Fetches the\n" +
			"habit, then records a completion carrying its id alongside the name and\n" +
			"category it had at the time.\n\n" +
			"--date fills in a day you forgot. A future day is rejected.",
		Example: "  # done just now\n  icb habits complete 5\n\n" +
			"  # a day you forgot to record\n  icb habits complete 5 --date 2026-08-21",
		Args: usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("habit id", args[0])
			if err != nil {
				return err
			}
			completeDate, err := habitCompleteDate(date, time.Now())
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			habit, err := client.GetHabit(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			completed, err := client.CompleteHabit(cmd.Context(), api.HabitCompletedCreateInput{
				HabitID:      &habit.ID,
				Name:         habit.Name,
				CategoryID:   habit.CategoryID,
				CompleteDate: completeDate,
			})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), completed)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Completed habit %q on %s (completion id %d)\n",
				completed.Name, completed.CompleteDate, completed.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&date, "date", "", "Day the habit was done (YYYY-MM-DD); defaults to today")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the completion as JSON to stdout")
	return cmd
}

// errDateFormat and errDateInFuture are the two ways --date is refused. They are
// sentinels so a caller branches on which refusal it hit rather than on the wording.
var (
	errDateFormat   = errors.New("--date is not a calendar day")
	errDateInFuture = errors.New("--date is in the future")
)

// habitCompleteDate resolves --date against now into the YYYY-MM-DD day sent to
// the API. Empty means today in now's zone. A day after today is refused,
// because a habit cannot have been done yet.
func habitCompleteDate(date string, now time.Time) (string, error) {
	today := now.Format(dayLayout)
	if date == "" {
		return today, nil
	}
	day, err := time.Parse(dayLayout, date)
	if err != nil {
		return "", usageError{fmt.Errorf("%w: %q — expected YYYY-MM-DD", errDateFormat, date)}
	}
	// YYYY-MM-DD compares as a string in calendar order.
	normalized := day.Format(dayLayout)
	if normalized > today {
		return "", usageError{fmt.Errorf("%w: %s — a habit cannot be completed ahead of time", errDateInFuture, date)}
	}
	return normalized, nil
}

func newHabitsCategoriesCommand() *cobra.Command {
	var (
		current bool
		asJSON  bool
	)
	cmd := &cobra.Command{
		Use:     "categories",
		Short:   "List habit categories",
		Example: "  icb habits categories\n  icb habits categories --current",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			categories, err := client.ListHabitCategories(cmd.Context(), boolFlagPtr(cmd, "current"), nil)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), categories)
			}
			printHabitCategoriesTable(cmd.OutOrStdout(), categories)
			return nil
		},
	}
	cmd.Flags().BoolVar(&current, "current", false, "Filter by current status")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output categories as JSON to stdout")
	return cmd
}

func newHabitsCompletedCommand() *cobra.Command {
	var (
		start  string
		end    string
		first  bool
		last   bool
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "completed",
		Short:   "List habit completions",
		Long:    "List completions. With no flags, all are returned; --first/--last give the\nsingle earliest/most-recent; --start/--end bound a date range.",
		Example: "  icb habits completed --last",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			q := api.CompletedTasksQuery{StartDate: start, EndDate: end, First: first, Last: last}
			completed, err := client.ListCompletedHabits(cmd.Context(), q)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), completed)
			}
			printHabitCompletedTable(cmd.OutOrStdout(), completed)
			return nil
		},
	}
	cmd.Flags().StringVar(&start, "start", "", "Range start (ISO 8601)")
	cmd.Flags().StringVar(&end, "end", "", "Range end (ISO 8601)")
	cmd.Flags().BoolVar(&first, "first", false, "Only the earliest completion")
	cmd.Flags().BoolVar(&last, "last", false, "Only the most recent completion")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output completions as JSON to stdout")
	return cmd
}

// boolFlagPtr returns a *bool for a bool flag: nil when unset (so the caller
// omits the filter), or a pointer to its value when the user passed it.
func boolFlagPtr(cmd *cobra.Command, name string) *bool {
	if !cmd.Flags().Changed(name) {
		return nil
	}
	v, _ := cmd.Flags().GetBool(name)
	return &v
}

func printHabitsTable(out io.Writer, habits []api.Habit) {
	if len(habits) == 0 {
		_, _ = fmt.Fprintln(out, "No habits.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tNAME\tCURRENT\tCATEGORY")
	for _, h := range habits {
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\t%s\n", h.ID, h.Name, yesNo(h.IsCurrent), h.Category.Name)
	}
	_ = tw.Flush()
}

func printHabitDetail(out io.Writer, h api.Habit) {
	_, _ = fmt.Fprintf(out, "%s\n", h.Name)
	_, _ = fmt.Fprintf(out, "  id:       %d\n", h.ID)
	_, _ = fmt.Fprintf(out, "  category: %s (id %d)\n", h.Category.Name, h.CategoryID)
	_, _ = fmt.Fprintf(out, "  current:  %s\n", yesNo(h.IsCurrent))
}

func printHabitCategoriesTable(out io.Writer, categories []api.HabitCategory) {
	if len(categories) == 0 {
		_, _ = fmt.Fprintln(out, "No habit categories.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tNAME\tCURRENT")
	for _, c := range categories {
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\n", c.ID, c.Name, yesNo(c.IsCurrent))
	}
	_ = tw.Flush()
}

func printHabitCompletedTable(out io.Writer, completed []api.HabitCompleted) {
	if len(completed) == 0 {
		_, _ = fmt.Fprintln(out, "No completions.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tNAME\tDATE\tCATEGORY")
	for _, c := range completed {
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\t%s\n", c.ID, c.Name, c.CompleteDate, c.Category.Name)
	}
	_ = tw.Flush()
}
