package cli

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

// limitUsage is the one description every --limit carries. `cli-design.md`
// § "A flag means one thing across every verb of a resource" is why it is shared
// text rather than a sentence written per command: a caller who has read it once
// on `tasks list` has read it everywhere.
const limitUsage = "Return at most this many rows"

// limitValue parses --limit and refuses a negative, which is the floor a row
// count owes. pflag has no minimum, so the parser is this Set method: without
// it a -1 reaches a slice expression, and `items[:-1]` panics where a usage
// error was the answer.
type limitValue struct{ target *int }

func (v limitValue) String() string { return strconv.Itoa(*v.target) }

func (v limitValue) Type() string { return "int" }

func (v limitValue) Set(raw string) error {
	n, err := strconv.Atoi(raw)
	if err != nil {
		return fmt.Errorf("invalid limit %q: a row count is a whole number", raw)
	}
	if n < 0 {
		return fmt.Errorf("invalid limit %d: a row count is zero or more", n)
	}
	*v.target = n
	return nil
}

// addLimitFlag declares --limit/-n on a list command, defaulting to fallback.
// The shorthand is part of the flag, per `cli-design.md` § "`--follow`/`-f`
// defaults to false; `--limit`/`-n` goes on every list".
//
// The default is seeded into target before the flag is registered, because
// pflag reads DefValue off the value's String method at that moment. A command
// declaring its own IntVarP is how two of them came to carry their own usage
// text, so every --limit in the CLI is declared here.
func addLimitFlag(cmd *cobra.Command, target *int, fallback int) {
	*target = fallback
	cmd.Flags().VarP(limitValue{target: target}, "limit", "n", limitUsage)
}

// limitFlag returns a *int for the --limit flag, or nil when it was not set (so
// the client omits the query param and the API returns everything).
//
// A limit is a row count and 0 is a count a caller can mean, so --limit 0 is a
// pointer to zero that reaches the server as `limit=0` and answers with
// nothing. Absence is what asks for every row, and it is the only thing that
// does.
func limitFlag(cmd *cobra.Command) *int {
	if !cmd.Flags().Changed("limit") {
		return nil
	}
	v, _ := cmd.Flags().GetInt("limit")
	return &v
}
