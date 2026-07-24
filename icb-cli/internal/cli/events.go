package cli

import (
	"fmt"
	"io"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newEventsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "events",
		Short: "List, inspect, and manage your events",
		Long:  "Work with events — dated happenings with a venue, cost, and RSVP — in the\nichrisbirch API as yourself. Requires a logged-in session (`icb auth login`).",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(
		newEventsListCommand(),
		newEventsViewCommand(),
		newEventsCreateCommand(),
		newEventsEditCommand(),
		newEventsAttendCommand(),
		newEventsDeleteCommand(),
	)
	return cmd
}

func newEventsListCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List all events by date",
		Example: "  icb events list\n  icb events list --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			events, err := client.ListEvents(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), events)
			}
			printEventsTable(cmd.OutOrStdout(), events)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output events as JSON to stdout")
	return cmd
}

func newEventsViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <event-id>",
		Short:   "Show a single event",
		Example: "  icb events view 7",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("event id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			event, err := client.GetEvent(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), event)
			}
			printEventDetail(cmd.OutOrStdout(), event)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the event as JSON to stdout")
	return cmd
}

func newEventsCreateCommand() *cobra.Command {
	var (
		name      string
		date      string
		venue     string
		cost      float64
		attending bool
		url       string
		notes     string
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "create --name <name> --date <when> --venue <venue> --cost <n> [flags]",
		Short:   "Create a new event",
		Example: "  icb events create --name \"Show\" --date \"2026-09-01 20:00\" --venue \"The Hall\" --cost 45 --attending",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if name == "" {
				return usageError{fmt.Errorf("--name is required")}
			}
			if date == "" {
				return usageError{fmt.Errorf("--date is required")}
			}
			if venue == "" {
				return usageError{fmt.Errorf("--venue is required")}
			}
			in := api.EventCreateInput{Name: name, Date: date, Venue: venue, Cost: cost, Attending: attending}
			if cmd.Flags().Changed("url") {
				in.URL = &url
			}
			if cmd.Flags().Changed("notes") {
				in.Notes = &notes
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			event, err := client.CreateEvent(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), event)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Created event %q at %s (id %d)\n", event.Name, event.Date.Format("2006-01-02 15:04"), event.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Event name (required)")
	cmd.Flags().StringVar(&date, "date", "", "Event date/time, e.g. \"2026-09-01 20:00\" (required)")
	cmd.Flags().StringVar(&venue, "venue", "", "Venue (required)")
	cmd.Flags().Float64Var(&cost, "cost", 0, "Cost")
	cmd.Flags().BoolVar(&attending, "attending", false, "Whether you are attending")
	cmd.Flags().StringVar(&url, "url", "", "Event URL")
	cmd.Flags().StringVar(&notes, "notes", "", "Markdown notes")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created event as JSON to stdout")
	return cmd
}

func newEventsEditCommand() *cobra.Command {
	var (
		name      string
		date      string
		venue     string
		cost      float64
		attending bool
		url       string
		notes     string
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "edit <event-id> [flags]",
		Short:   "Change fields on an existing event",
		Long:    "Update only the fields whose flags you pass.",
		Example: "  icb events edit 7 --cost 50 --attending",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("event id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.EventUpdateInput{}
			if f.Changed("name") {
				in.Name = &name
			}
			if f.Changed("date") {
				in.Date = &date
			}
			if f.Changed("venue") {
				in.Venue = &venue
			}
			if f.Changed("cost") {
				in.Cost = &cost
			}
			if f.Changed("attending") {
				in.Attending = &attending
			}
			if f.Changed("url") {
				in.URL = &url
			}
			if f.Changed("notes") {
				in.Notes = &notes
			}
			if (in == api.EventUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			event, err := client.UpdateEvent(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), event)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Updated event %q (id %d)\n", event.Name, event.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New event name")
	cmd.Flags().StringVar(&date, "date", "", "New date/time")
	cmd.Flags().StringVar(&venue, "venue", "", "New venue")
	cmd.Flags().Float64Var(&cost, "cost", 0, "New cost")
	cmd.Flags().BoolVar(&attending, "attending", false, "Set attendance")
	cmd.Flags().StringVar(&url, "url", "", "New URL")
	cmd.Flags().StringVar(&notes, "notes", "", "New markdown notes")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated event as JSON to stdout")
	return cmd
}

func newEventsAttendCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "attend <event-id>",
		Short:   "Mark yourself as attending an event",
		Example: "  icb events attend 7",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("event id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			event, err := client.AttendEvent(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), event)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Attending event %q (id %d)\n", event.Name, event.ID)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the event as JSON to stdout")
	return cmd
}

func newEventsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <event-id>",
		Short:   "Delete an event",
		Example: "  icb events delete 7 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("event id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			event, err := client.GetEvent(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete event %q (id %d)?", event.Name, event.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteEvent(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted event %q (id %d)\n", event.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func printEventsTable(out io.Writer, events []api.Event) {
	if len(events) == 0 {
		fmt.Fprintln(out, "No events.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tDATE\tGOING\tVENUE\tNAME")
	for _, e := range events {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%s\t%s\n", e.ID, e.Date.Format("2006-01-02 15:04"), yesNo(e.Attending), e.Venue, e.Name)
	}
	_ = tw.Flush()
}

func printEventDetail(out io.Writer, e api.Event) {
	fmt.Fprintf(out, "%s\n", e.Name)
	fmt.Fprintf(out, "  id:        %d\n", e.ID)
	fmt.Fprintf(out, "  date:      %s\n", e.Date.Format("2006-01-02 15:04"))
	fmt.Fprintf(out, "  venue:     %s\n", e.Venue)
	fmt.Fprintf(out, "  cost:      %.2f\n", e.Cost)
	fmt.Fprintf(out, "  attending: %s\n", yesNo(e.Attending))
	if u := strValue(e.URL); u != "" {
		fmt.Fprintf(out, "  url:       %s\n", u)
	}
	if n := strValue(e.Notes); n != "" {
		fmt.Fprintf(out, "  notes:     %s\n", n)
	}
}

func yesNo(b bool) string {
	if b {
		return "yes"
	}
	return "no"
}
