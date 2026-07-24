package cli

import (
	"fmt"
	"io"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newAutotasksCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "autotasks",
		Short: "Inspect your recurring task templates",
		Long: "View the auto-tasks the scheduler uses to spawn recurring tasks. This group\n" +
			"is read-only — the scheduler owns creation and run bookkeeping. Requires a\n" +
			"logged-in session (`icb auth login`).",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newAutotasksListCommand(),
		newAutotasksViewCommand(),
	)
	return cmd
}

func newAutotasksListCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List recurring task templates",
		Example: "  icb autotasks list\n  icb autotasks list --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			autotasks, err := client.ListAutoTasks(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), autotasks)
			}
			printAutotasksTable(cmd.OutOrStdout(), autotasks)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output auto-tasks as JSON to stdout")
	return cmd
}

func newAutotasksViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <autotask-id>",
		Short:   "Show a single recurring task template",
		Example: "  icb autotasks view 2",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("autotask id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			autotask, err := client.GetAutoTask(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), autotask)
			}
			printAutotaskDetail(cmd.OutOrStdout(), autotask)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the auto-task as JSON to stdout")
	return cmd
}

func printAutotasksTable(out io.Writer, autotasks []api.AutoTask) {
	if len(autotasks) == 0 {
		fmt.Fprintln(out, "No auto-tasks.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tPRIORITY\tFREQUENCY\tMAX\tRUNS\tNAME\tCATEGORY")
	for _, a := range autotasks {
		fmt.Fprintf(tw, "%d\t%d\t%s\t%d\t%d\t%s\t%s\n",
			a.ID, a.Priority, a.Frequency, a.MaxConcurrent, a.RunCount, a.Name, a.Category)
	}
	_ = tw.Flush()
}

func printAutotaskDetail(out io.Writer, a api.AutoTask) {
	fmt.Fprintf(out, "%s\n", a.Name)
	fmt.Fprintf(out, "  id:          %d\n", a.ID)
	fmt.Fprintf(out, "  category:    %s\n", a.Category)
	fmt.Fprintf(out, "  priority:    %d\n", a.Priority)
	fmt.Fprintf(out, "  frequency:   %s\n", a.Frequency)
	fmt.Fprintf(out, "  max concur.: %d\n", a.MaxConcurrent)
	fmt.Fprintf(out, "  run count:   %d\n", a.RunCount)
	fmt.Fprintf(out, "  first run:   %s\n", a.FirstRunDate.Format("2006-01-02"))
	fmt.Fprintf(out, "  last run:    %s\n", a.LastRunDate.Format("2006-01-02"))
	if s := strValue(a.Notes); s != "" {
		fmt.Fprintf(out, "  notes:       %s\n", s)
	}
}
