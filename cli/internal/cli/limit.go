package cli

import "github.com/spf13/cobra"

// limitUsage is the one description every --limit carries. `cli-design.md`
// § "A flag means one thing across every verb of a resource" is why it is shared
// text rather than a sentence written per command: a caller who has read it once
// on `tasks list` has read it everywhere.
const limitUsage = "Return at most this many rows (0 for no cap)"

// addLimitFlag declares --limit/-n on a list command. The shorthand is part of
// the flag, per `cli-design.md` § "`--follow`/`-f` defaults to false;
// `--limit`/`-n` goes on every list".
//
// The default is 0 rather than a number, so an unasked-for limit and an explicit
// "no cap" agree: neither caps anything.
func addLimitFlag(cmd *cobra.Command, target *int) {
	cmd.Flags().IntVarP(target, "limit", "n", 0, limitUsage)
}

// limitFlag returns a *int for the --limit flag, or nil when it was not set (so
// the client omits the query param and the API returns everything).
//
// An explicit --limit 0 is a pointer to zero, which applyLimit then declines to
// send — "all" reaching the server as an absent parameter rather than as a
// `LIMIT 0` that would answer with nothing.
func limitFlag(cmd *cobra.Command) *int {
	if !cmd.Flags().Changed("limit") {
		return nil
	}
	v, _ := cmd.Flags().GetInt("limit")
	return &v
}
