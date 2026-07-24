package cli

import (
	"fmt"
	"io"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newHabitsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "habits",
		Short: "List, inspect, complete, and manage your habits",
		Long:  "Work with habits, their categories, and completions in the ichrisbirch API\nas yourself. Requires a logged-in session (`icb auth login`).",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(
		newHabitsListCommand(),
		newHabitsViewCommand(),
		newHabitsCreateCommand(),
		newHabitsEditCommand(),
		newHabitsDeleteCommand(),
		newHabitsCompleteCommand(),
		newHabitsCategoriesCommand(),
		newHabitsCompletedCommand(),
	)
	return cmd
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
	cmd.Flags().IntVar(&limit, "limit", 0, "Maximum number of habits to return")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output habits as JSON to stdout")
	return cmd
}

func newHabitsViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <habit-id>",
		Short:   "Show a single habit",
		Example: "  icb habits view 5",
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
			fmt.Fprintf(cmd.OutOrStdout(), "Created habit %q (id %d)\n", habit.Name, habit.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Habit name (required)")
	cmd.Flags().IntVar(&category, "category", 0, "Category id (required)")
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
			fmt.Fprintf(cmd.OutOrStdout(), "Updated habit %q (id %d)\n", habit.Name, habit.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New habit name")
	cmd.Flags().IntVar(&category, "category", 0, "New category id")
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
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete habit %q (id %d)?", habit.Name, habit.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteHabit(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted habit %q (id %d)\n", habit.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func newHabitsCompleteCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "complete <habit-id>",
		Short:   "Record a completion of a habit (now)",
		Long:    "Mark a habit done as of now. Fetches the habit for its name and category,\nthen records a completion.",
		Example: "  icb habits complete 5",
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
			completed, err := client.CompleteHabit(cmd.Context(), api.HabitCompletedCreateInput{
				Name:         habit.Name,
				CategoryID:   habit.CategoryID,
				CompleteDate: time.Now().Format(time.RFC3339),
			})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), completed)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Completed habit %q on %s (completion id %d)\n",
				completed.Name, completed.CompleteDate.Format("2006-01-02"), completed.ID)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the completion as JSON to stdout")
	return cmd
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
		fmt.Fprintln(out, "No habits.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tCURRENT\tCATEGORY\tNAME")
	for _, h := range habits {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%s\n", h.ID, yesNo(h.IsCurrent), h.Category.Name, h.Name)
	}
	_ = tw.Flush()
}

func printHabitDetail(out io.Writer, h api.Habit) {
	fmt.Fprintf(out, "%s\n", h.Name)
	fmt.Fprintf(out, "  id:       %d\n", h.ID)
	fmt.Fprintf(out, "  category: %s (id %d)\n", h.Category.Name, h.CategoryID)
	fmt.Fprintf(out, "  current:  %s\n", yesNo(h.IsCurrent))
}

func printHabitCategoriesTable(out io.Writer, categories []api.HabitCategory) {
	if len(categories) == 0 {
		fmt.Fprintln(out, "No habit categories.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tCURRENT\tNAME")
	for _, c := range categories {
		fmt.Fprintf(tw, "%d\t%s\t%s\n", c.ID, yesNo(c.IsCurrent), c.Name)
	}
	_ = tw.Flush()
}

func printHabitCompletedTable(out io.Writer, completed []api.HabitCompleted) {
	if len(completed) == 0 {
		fmt.Fprintln(out, "No completions.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tDATE\tCATEGORY\tNAME")
	for _, c := range completed {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%s\n", c.ID, c.CompleteDate.Format("2006-01-02"), c.Category.Name, c.Name)
	}
	_ = tw.Flush()
}
