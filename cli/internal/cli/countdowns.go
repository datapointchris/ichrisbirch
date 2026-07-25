package cli

import (
	"fmt"
	"io"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newCountdownsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "countdowns",
		Short: "List, inspect, and manage your countdowns",
		Long:  "Work with countdowns — named future dates — in the ichrisbirch API as\nyourself. Requires a logged-in session (`icb auth login`).",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(
		newCountdownsListCommand(),
		newCountdownsViewCommand(),
		newCountdownsCreateCommand(),
		newCountdownsEditCommand(),
		newCountdownsDeleteCommand(),
	)
	return cmd
}

func newCountdownsListCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List all countdowns by due date",
		Example: "  icb countdowns list\n  icb countdowns list --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			countdowns, err := client.ListCountdowns(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), countdowns)
			}
			printCountdownsTable(cmd.OutOrStdout(), countdowns)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output countdowns as JSON to stdout")
	return cmd
}

func newCountdownsViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <countdown-id>",
		Short:   "Show a single countdown",
		Example: "  icb countdowns view 3",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("countdown id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			countdown, err := client.GetCountdown(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), countdown)
			}
			printCountdownDetail(cmd.OutOrStdout(), countdown)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the countdown as JSON to stdout")
	return cmd
}

func newCountdownsCreateCommand() *cobra.Command {
	var (
		name   string
		due    string
		notes  string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "create --name <name> --due <YYYY-MM-DD> [flags]",
		Short:   "Create a new countdown",
		Example: "  icb countdowns create --name \"Lease ends\" --due 2027-03-01",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return usageError{fmt.Errorf("--name is required")}
			}
			if due == "" {
				return usageError{fmt.Errorf("--due is required (YYYY-MM-DD)")}
			}
			if err := validateDate(due); err != nil {
				return usageError{err}
			}
			in := api.CountdownCreateInput{Name: name, DueDate: due}
			if cmd.Flags().Changed("notes") {
				in.Notes = &notes
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			countdown, err := client.CreateCountdown(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), countdown)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Created countdown %q due %s (id %d)\n", countdown.Name, countdown.DueDate, countdown.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Countdown name (required)")
	cmd.Flags().StringVar(&due, "due", "", "Due date, YYYY-MM-DD (required)")
	cmd.Flags().StringVar(&notes, "notes", "", "Markdown notes")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created countdown as JSON to stdout")
	return cmd
}

func newCountdownsEditCommand() *cobra.Command {
	var (
		name   string
		due    string
		notes  string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "edit <countdown-id> [flags]",
		Short:   "Change fields on an existing countdown",
		Long:    "Update only the fields whose flags you pass.",
		Example: "  icb countdowns edit 3 --due 2027-04-01",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("countdown id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.CountdownUpdateInput{}
			if f.Changed("name") {
				in.Name = &name
			}
			if f.Changed("notes") {
				in.Notes = &notes
			}
			if f.Changed("due") {
				if err := validateDate(due); err != nil {
					return usageError{err}
				}
				in.DueDate = &due
			}
			if in == (api.CountdownUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass at least one of --name/--due/--notes")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			countdown, err := client.UpdateCountdown(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), countdown)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Updated countdown %q (id %d)\n", countdown.Name, countdown.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New countdown name")
	cmd.Flags().StringVar(&due, "due", "", "New due date, YYYY-MM-DD")
	cmd.Flags().StringVar(&notes, "notes", "", "New markdown notes")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated countdown as JSON to stdout")
	return cmd
}

func newCountdownsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <countdown-id>",
		Short:   "Delete a countdown",
		Example: "  icb countdowns delete 3 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("countdown id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			countdown, err := client.GetCountdown(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete countdown %q (id %d)?", countdown.Name, countdown.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteCountdown(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted countdown %q (id %d)\n", countdown.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func printCountdownsTable(out io.Writer, countdowns []api.Countdown) {
	if len(countdowns) == 0 {
		fmt.Fprintln(out, "No countdowns.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tDUE\tIN\tNAME")
	for _, c := range countdowns {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%s\n", c.ID, c.DueDate, daysUntil(c.DueDate), c.Name)
	}
	_ = tw.Flush()
}

func printCountdownDetail(out io.Writer, c api.Countdown) {
	fmt.Fprintf(out, "%s\n", c.Name)
	fmt.Fprintf(out, "  id:   %d\n", c.ID)
	fmt.Fprintf(out, "  due:  %s (%s)\n", c.DueDate, daysUntil(c.DueDate))
	if n := strValue(c.Notes); n != "" {
		fmt.Fprintf(out, "  notes: %s\n", n)
	}
}

// daysUntil renders a human "in N days" / "N days ago" for a YYYY-MM-DD date, or
// the raw value if it does not parse.
func daysUntil(date string) string {
	due, err := time.Parse("2006-01-02", date)
	if err != nil {
		return "?"
	}
	today := time.Now().Truncate(24 * time.Hour)
	days := int(due.Truncate(24*time.Hour).Sub(today).Hours() / 24)
	switch {
	case days == 0:
		return "today"
	case days > 0:
		return fmt.Sprintf("in %dd", days)
	default:
		return fmt.Sprintf("%dd ago", -days)
	}
}

// validateDate enforces YYYY-MM-DD so a malformed value fails locally as a usage
// error rather than reaching the API.
func validateDate(s string) error {
	if _, err := time.Parse("2006-01-02", s); err != nil {
		return fmt.Errorf("invalid date %q: want YYYY-MM-DD", s)
	}
	return nil
}
