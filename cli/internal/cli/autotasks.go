package cli

import (
	"fmt"
	"io"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func newAutotasksCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "autotasks",
		Short: "Inspect your recurring task templates",
		Long: "The templates behind your recurring tasks: what respawns, how often, and when\n" +
			"each last ran. Read-only — the scheduler is what creates and completes them.",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newAutotasksListCommand(),
		newAutotasksShowCommand(),
	)
	return cmd
}

func newAutotasksListCommand() *cobra.Command {
	var (
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List recurring task templates",
		Long: "Templates come back most recently run first, so --limit takes the ones that\n" +
			"fired last rather than an arbitrary slice.",
		Example: "  icb autotasks list\n  icb autotasks list --limit 5\n  icb autotasks list --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			autotasks, err := client.ListAutoTasks(cmd.Context(), limitFlag(cmd))
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
	addLimitFlag(cmd, &limit)
	return cmd
}

func newAutotasksShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <autotask-id>",
		Short:   "Show a single recurring task template",
		Example: "  icb autotasks show 2",
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
		_, _ = fmt.Fprintln(out, "No auto-tasks.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tPRIORITY\tFREQUENCY\tMAX\tRUNS\tNAME\tCATEGORY")
	for _, a := range autotasks {
		_, _ = fmt.Fprintf(tw, "%d\t%d\t%s\t%d\t%d\t%s\t%s\n",
			a.ID, a.Priority, a.Frequency, a.MaxConcurrent, a.RunCount, a.Name, a.Category)
	}
	_ = tw.Flush()
}

func printAutotaskDetail(out io.Writer, a api.AutoTask) {
	_, _ = fmt.Fprintf(out, "%s\n", a.Name)
	_, _ = fmt.Fprintf(out, "  id:          %d\n", a.ID)
	_, _ = fmt.Fprintf(out, "  category:    %s\n", a.Category)
	_, _ = fmt.Fprintf(out, "  priority:    %d\n", a.Priority)
	_, _ = fmt.Fprintf(out, "  frequency:   %s\n", a.Frequency)
	_, _ = fmt.Fprintf(out, "  max concur.: %d\n", a.MaxConcurrent)
	_, _ = fmt.Fprintf(out, "  run count:   %d\n", a.RunCount)
	_, _ = fmt.Fprintf(out, "  first run:   %s\n", a.FirstRunDate.Format("2006-01-02"))
	_, _ = fmt.Fprintf(out, "  last run:    %s\n", a.LastRunDate.Format("2006-01-02"))
	if s := strValue(a.Notes); s != "" {
		_, _ = fmt.Fprintf(out, "  notes:       %s\n", s)
	}
}
