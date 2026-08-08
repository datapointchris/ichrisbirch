package cli

import (
	"fmt"
	"io"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func newPatternsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "patterns",
		Short: "Capture and review the observations you want to correlate",
		Long:  "Fragments noticed in passing — what you ate, how you slept, when the\nheadache started. Not tasks and not journal entries: the point is having\nenough of them, over enough time, to see what goes with what.",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(
		newPatternsListCommand(),
		newPatternsShowCommand(),
		newPatternsCreateCommand(),
		newPatternsEditCommand(),
		newPatternsDeleteCommand(),
	)
	return cmd
}

func newPatternsListCommand() *cobra.Command {
	var (
		search string
		limit  int
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "list [flags]",
		Short:   "List patterns, newest first",
		Example: "  icb patterns list\n  icb patterns list --search heartburn\n  icb patterns list --limit 20 --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			patterns, err := client.ListPatterns(cmd.Context(), api.PatternListOptions{Search: search, Limit: limit})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), patterns)
			}
			printPatternsTable(cmd.OutOrStdout(), patterns)
			return nil
		},
	}
	cmd.Flags().StringVar(&search, "search", "", "Only patterns whose message contains this text")
	cmd.Flags().IntVar(&limit, "limit", 0, "Return at most this many patterns")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output patterns as JSON to stdout")
	return cmd
}

func newPatternsShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <pattern-id>",
		Short:   "Show a single pattern",
		Example: "  icb patterns show 12",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("pattern id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			pattern, err := client.GetPattern(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), pattern)
			}
			printPatternDetail(cmd.OutOrStdout(), pattern)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the pattern as JSON to stdout")
	return cmd
}

func newPatternsCreateCommand() *cobra.Command {
	var (
		recordedAt string
		asJSON     bool
	)
	cmd := &cobra.Command{
		Use:   "create <message>",
		Short: "Capture a pattern",
		// The message is positional rather than a flag because capture happens
		// mid-flow: anything longer than the thought itself does not get typed.
		Long:    "The timestamp is the server's unless --at is given, so capturing is one argument.",
		Example: "  icb patterns create \"coffee at 3pm, wired until midnight\"\n  icb patterns create \"ate late\" --at 2026-08-06T21:30:00Z",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			in := api.PatternCreateInput{Message: args[0]}
			if cmd.Flags().Changed("at") {
				if err := validateTimestamp(recordedAt); err != nil {
					return usageError{err}
				}
				in.RecordedAt = &recordedAt
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			pattern, err := client.CreatePattern(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), pattern)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Captured pattern %d\n", pattern.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&recordedAt, "at", "", "When it happened, RFC3339 (default: now)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created pattern as JSON to stdout")
	return cmd
}

func newPatternsEditCommand() *cobra.Command {
	var (
		message    string
		recordedAt string
		asJSON     bool
	)
	cmd := &cobra.Command{
		Use:     "edit <pattern-id> [flags]",
		Short:   "Change fields on an existing pattern",
		Long:    "Update only the fields whose flags you pass.",
		Example: "  icb patterns edit 12 --message \"coffee at 3pm, not 4\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("pattern id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.PatternUpdateInput{}
			if f.Changed("message") {
				in.Message = &message
			}
			if f.Changed("at") {
				if err := validateTimestamp(recordedAt); err != nil {
					return usageError{err}
				}
				in.RecordedAt = &recordedAt
			}
			if in == (api.PatternUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass at least one of --message/--at")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			pattern, err := client.UpdatePattern(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), pattern)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated pattern %d\n", pattern.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&message, "message", "", "New message")
	cmd.Flags().StringVar(&recordedAt, "at", "", "New timestamp, RFC3339")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated pattern as JSON to stdout")
	return cmd
}

func newPatternsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <pattern-id>",
		Short:   "Delete a pattern",
		Example: "  icb patterns delete 12 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("pattern id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			pattern, err := client.GetPattern(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete pattern %d (%s)?", pattern.ID, truncate(pattern.Message, 60)))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeletePattern(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted pattern %d\n", id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func printPatternsTable(out io.Writer, patterns []api.Pattern) {
	if len(patterns) == 0 {
		_, _ = fmt.Fprintln(out, "No patterns.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tWHEN\tMESSAGE")
	for _, p := range patterns {
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\n", p.ID, shortTimestamp(p.RecordedAt), truncate(p.Message, 80))
	}
	_ = tw.Flush()
}

func printPatternDetail(out io.Writer, p api.Pattern) {
	_, _ = fmt.Fprintf(out, "%s\n", p.Message)
	_, _ = fmt.Fprintf(out, "  id:   %d\n", p.ID)
	_, _ = fmt.Fprintf(out, "  when: %s\n", shortTimestamp(p.RecordedAt))
}

// shortTimestamp renders an RFC3339 timestamp as local "2006-01-02 15:04", or
// the raw value if it does not parse.
func shortTimestamp(ts string) string {
	parsed, err := time.Parse(time.RFC3339, ts)
	if err != nil {
		return ts
	}
	return parsed.Local().Format("2006-01-02 15:04")
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-1] + "…"
}

func validateTimestamp(s string) error {
	if _, err := time.Parse(time.RFC3339, s); err != nil {
		return fmt.Errorf("invalid timestamp %q: want RFC3339, e.g. 2026-08-06T21:30:00Z", s)
	}
	return nil
}
