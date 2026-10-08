package cli

import (
	"errors"
	"fmt"
	"io"
	"slices"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

var initiativeHints = []string{"Finished initiatives are hidden: icb issues initiatives list --status all"}

func newIssueInitiativesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "initiatives",
		Short: "Group the issues that ship one outcome",
		Long: "An initiative is an outcome that finishes, and most issues belong to none.\n" +
			"An issue with no priority of its own takes its active initiative's. A\n" +
			"finished initiative takes no new issues, and its own stay where they are.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd, initiativeHints...)
	cmd.AddCommand(
		newInitiativesListCommand(),
		newInitiativesShowCommand(),
		newInitiativesCreateCommand(),
		newInitiativesEditCommand(),
		newInitiativesCompleteCommand(),
		newInitiativesDropCommand(),
		newInitiativesReopenCommand(),
		newInitiativesDeleteCommand(),
	)
	return cmd
}

func newInitiativesListCommand() *cobra.Command {
	var (
		asJSON           bool
		initiativeStatus string
		limit            int
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List the active initiatives in the order to work them",
		Long: "Active initiatives by priority, then position. Completed and dropped ones are\n" +
			"hidden until --status asks for them, and come after, latest first.",
		Example: "  icb issues initiatives list\n  icb issues initiatives list --status all --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if cmd.Flags().Changed("status") && !slices.Contains(api.InitiativeStatuses, initiativeStatus) {
				return usageError{fmt.Errorf("unknown status %q — one of: %s", initiativeStatus, strings.Join(api.InitiativeStatuses, ", "))}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			initiatives, err := client.ListInitiatives(cmd.Context(), initiativeStatus, limitFlag(cmd))
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), initiatives)
			}
			printInitiativesTable(cmd.OutOrStdout(), initiatives)
			if !cmd.Flags().Changed("status") {
				_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\n"+initiativeHints[0])
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&initiativeStatus, "status", "", "One of: "+strings.Join(api.InitiativeStatuses, ", ")+" (default active)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output initiatives as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newInitiativesShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <initiative>",
		Short:   "Show an initiative and its unclosed issues in queue order",
		Example: "  icb issues initiatives show \"Ship the tracker\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			initiative, err := client.GetInitiative(cmd.Context(), args[0])
			if err != nil {
				return handleArgumentAPIError(err)
			}
			issues, err := client.ListIssues(cmd.Context(), api.IssueFilter{Initiative: initiative.ID}, "", "", issueZone(), nil)
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), struct {
					api.Initiative
					Issues []api.Issue `json:"issues"`
				}{initiative, issues})
			}
			printInitiativeDetail(cmd.OutOrStdout(), initiative)
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "\nUnclosed issues (%d):\n", len(issues))
			if len(issues) == 0 {
				_, _ = fmt.Fprintln(cmd.OutOrStdout(), "  (none)")
				return nil
			}
			printIssuesTable(cmd.OutOrStdout(), issues, time.Now())
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the initiative and its issues as JSON to stdout")
	return cmd
}

func newInitiativesCreateCommand() *cobra.Command {
	var (
		name        string
		description string
		priority    string
		position    int
		asJSON      bool
	)
	cmd := &cobra.Command{
		Use:     "create --name <name> [flags]",
		Short:   "Start an initiative",
		Example: "  icb issues initiatives create --name \"Ship the tracker\" --priority high",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if strings.TrimSpace(name) == "" {
				return usageError{errors.New("--name is required")}
			}
			f := cmd.Flags()
			in := api.InitiativeCreateInput{Name: name, Description: valuedStrFlag(f, "description", &description)}
			if f.Changed("priority") {
				value, err := parsePriority(priority)
				if err != nil {
					return usageError{fmt.Errorf("--priority: %w", err)}
				}
				in.Priority = &value
			}
			if f.Changed("position") {
				in.Position = &position
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			initiative, err := client.CreateInitiative(cmd.Context(), in)
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), initiative)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Started initiative %q\n", initiative.Name)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Initiative name, unique among active ones (required)")
	cmd.Flags().StringVar(&description, "description", "", "The outcome, and how you will know it is done")
	cmd.Flags().StringVar(&priority, "priority", "", "One of: "+priorityChoices()+" (default none)")
	cmd.Flags().IntVar(&position, "position", 0, "Place among initiatives of its priority (default last)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the initiative as JSON to stdout")
	return cmd
}

func newInitiativesEditCommand() *cobra.Command {
	var (
		name        string
		description string
		priority    string
		position    int
		asJSON      bool
	)
	cmd := &cobra.Command{
		Use:   "edit <initiative> [flags]",
		Short: "Change an initiative's fields",
		Long: "Update only the fields whose flags you pass. --description \"\" clears it.\n" +
			"Status moves through complete, drop and reopen.",
		Example: "  icb issues initiatives edit \"Ship the tracker\" --priority urgent",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			if readFlagIntent(f, "name") == flagClears {
				return usageError{errors.New("--name cannot be emptied — every initiative carries one")}
			}
			in := api.InitiativeUpdateInput{
				Name:        valuedStrFlag(f, "name", &name),
				Description: valuedStrFlag(f, "description", &description),
			}
			if f.Changed("priority") {
				value, err := parsePriority(priority)
				if err != nil {
					return usageError{fmt.Errorf("--priority: %w", err)}
				}
				in.Priority = &value
			}
			if f.Changed("position") {
				in.Position = &position
			}
			var clear []string
			if readFlagIntent(f, "description") == flagClears {
				clear = append(clear, "description")
			}
			if in == (api.InitiativeUpdateInput{}) && len(clear) == 0 {
				return usageError{errors.New("nothing to change — pass at least one of --name/--description/--priority/--position")}
			}
			return runInitiativeUpdate(cmd, args[0], in, clear, asJSON, "Updated")
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New name")
	cmd.Flags().StringVar(&description, "description", "", "New description (empty clears)")
	cmd.Flags().StringVar(&priority, "priority", "", "One of: "+priorityChoices())
	cmd.Flags().IntVar(&position, "position", 0, "New place among initiatives of its priority")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the initiative as JSON to stdout")
	return cmd
}

func runInitiativeUpdate(cmd *cobra.Command, ref string, in api.InitiativeUpdateInput, clear []string, asJSON bool, verb string) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	initiative, err := client.UpdateInitiative(cmd.Context(), ref, in, clear)
	if err != nil {
		return handleArgumentAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), initiative)
	}
	_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s initiative %q (%s)\n", verb, initiative.Name, initiative.Status)
	return nil
}

func newInitiativesCompleteCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "complete <initiative>",
		Short:   "Mark an initiative's outcome reached, which hides it",
		Long:    "Its issues are left as they are: one still open was still open, and that is\nworth seeing.",
		Example: "  icb issues initiatives complete \"Ship the tracker\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			completed := "completed"
			return runInitiativeUpdate(cmd, args[0], api.InitiativeUpdateInput{Status: &completed}, nil, asJSON, "Completed")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the initiative as JSON to stdout")
	return cmd
}

func newInitiativesDropCommand() *cobra.Command {
	var (
		reason string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "drop <initiative> --reason <why>",
		Short:   "Close an initiative whose outcome you no longer want",
		Long:    "--reason is required: dropped-and-here-is-why closes the question, where\na bare drop invites it back.",
		Example: "  icb issues initiatives drop \"Rewrite the router\" --reason \"Traefik covers it\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(reason) == "" {
				return usageError{errors.New("--reason is required — say why it is dropped")}
			}
			dropped := "dropped"
			return runInitiativeUpdate(cmd, args[0], api.InitiativeUpdateInput{Status: &dropped, StatusReason: &reason}, nil, asJSON, "Dropped")
		},
	}
	cmd.Flags().StringVar(&reason, "reason", "", "Why it is dropped (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the initiative as JSON to stdout")
	return cmd
}

func newInitiativesReopenCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "reopen <initiative>",
		Short:   "Return a finished initiative to the active list",
		Long:    "Refused if an active initiative has taken the name in the meantime.",
		Example: "  icb issues initiatives reopen \"Ship the tracker\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			active := "active"
			return runInitiativeUpdate(cmd, args[0], api.InitiativeUpdateInput{Status: &active}, nil, asJSON, "Reopened")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the initiative as JSON to stdout")
	return cmd
}

func newInitiativesDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <initiative>",
		Short:   "Delete an initiative; its issues stay, belonging to none",
		Example: "  icb issues initiatives delete \"Ship the tracker\" --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			initiative, err := client.GetInitiative(cmd.Context(), args[0])
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if !yes {
				question := fmt.Sprintf("Delete initiative %q? Its %d %s will belong to none.",
					initiative.Name, initiative.IssueCount, plural(initiative.IssueCount, "issue", "issues"))
				ok, err := confirm(cmd, question)
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteInitiative(cmd.Context(), initiative.ID); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted initiative %q\n", initiative.Name)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// printInitiativesTable prints the name shell-quoted, so a row's handle pastes
// back as one argument.
func printInitiativesTable(out io.Writer, initiatives []api.Initiative) {
	if len(initiatives) == 0 {
		_, _ = fmt.Fprintln(out, "No initiatives.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "NAME\tPRIORITY\tSTATUS\tOPEN\tDONE\tCANCELED\tREPOS")
	for _, initiative := range initiatives {
		_, _ = fmt.Fprintf(tw, "%s\t%s\t%s\t%d\t%d\t%d\t%s\n",
			shellQuote(initiative.Name), priorityName(initiative.Priority), initiative.Status,
			initiative.OpenCount, initiative.CompletedCount, initiative.CanceledCount, repoList(initiative.Repos))
	}
	_ = tw.Flush()
}

func printInitiativeDetail(out io.Writer, initiative api.Initiative) {
	_, _ = fmt.Fprintf(out, "%s\n", initiative.Name)
	status := initiative.Status
	if initiative.ClosedTS != nil {
		status += " (" + localDay(*initiative.ClosedTS) + ")"
	}
	_, _ = fmt.Fprintf(out, "  status:    %s\n", status)
	if reason := strValue(initiative.StatusReason); reason != "" {
		_, _ = fmt.Fprintf(out, "  reason:    %s\n", reason)
	}
	_, _ = fmt.Fprintf(out, "  priority:  %s\n", priorityName(initiative.Priority))
	_, _ = fmt.Fprintf(out, "  issues:    %d (%d open, %d done, %d canceled)\n",
		initiative.IssueCount, initiative.OpenCount, initiative.CompletedCount, initiative.CanceledCount)
	_, _ = fmt.Fprintf(out, "  repos:     %s\n", repoList(initiative.Repos))
	if description := strValue(initiative.Description); description != "" {
		_, _ = fmt.Fprintf(out, "\nDescription:\n%s\n", indent(description, "  "))
	}
}
