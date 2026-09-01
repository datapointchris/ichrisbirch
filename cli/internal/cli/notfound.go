package cli

import (
	"errors"
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// notFoundHintsKey is the cobra annotation carrying the commands that find a
// valid id for the resource a command acts on.
const notFoundHintsKey = "icb.not-found-hints"

// withNotFoundHints records on cmd the commands a 404 under it should name, and
// returns cmd so it can be attached inline in an AddCommand list.
//
// Each hint is a sentence, a colon, and the command to run, matching the
// "Closed projects are hidden: icb projects list --status all" line the list
// commands already print when they hide rows.
//
// Cobra does not inherit annotations and the lookup takes the nearest ancestor
// carrying them, so a subcommand acting on a second kind of id names every way
// in: `complete-task` takes an item and a task, and lists both.
func withNotFoundHints(cmd *cobra.Command, hints ...string) *cobra.Command {
	if cmd.Annotations == nil {
		cmd.Annotations = map[string]string{}
	}
	cmd.Annotations[notFoundHintsKey] = strings.Join(hints, "\n")
	return cmd
}

// notFoundHintsFor returns the hints of the nearest command in cmd's ancestry
// carrying any, starting at cmd itself. `icb projects items` sits under
// `icb projects` and acts on a different resource, so the nearest set replaces
// the outer one rather than adding to it.
func notFoundHintsFor(cmd *cobra.Command) []string {
	for current := cmd; current != nil; current = current.Parent() {
		if joined := current.Annotations[notFoundHintsKey]; joined != "" {
			return strings.Split(joined, "\n")
		}
	}
	return nil
}

// notFoundError is a 404 written as the help screen for the failure in hand:
// the subject that was missing, then the commands that find a real one.
type notFoundError struct {
	subject string
	hints   []string
	cause   error
}

func (e *notFoundError) Error() string {
	return e.subject + "\n  " + strings.Join(e.hints, "\n  ")
}

// Unwrap keeps the *api.APIError reachable, so a caller can still branch on the
// status code rather than matching the rendered message.
func (e *notFoundError) Unwrap() error { return e.cause }

// hintNotFound rewrites a 404 leaving a command into the three things an error
// owes: what failed, what was expected, and the command that changes the
// situation. Anything else is returned untouched.
//
// The subject is the API's, not one built from the arguments, because only the
// API knows which id was missing: `icb projects items complete-task 598 4` can
// 404 on either number and the message names the one that did.
//
// The "API request failed (404 Not Found)" prefix goes with it. That reports how
// the answer arrived, and a 404 is an answer rather than a failure to get one.
func hintNotFound(cmd *cobra.Command, err error) error {
	var apiErr *api.APIError
	if !errors.As(err, &apiErr) || !apiErr.NotFound() {
		return err
	}
	hints := notFoundHintsFor(cmd)
	if len(hints) == 0 {
		return err
	}
	subject := apiErr.Message
	if subject == "" {
		subject = fmt.Sprintf("%s not found", cmd.Name())
	}
	return &notFoundError{subject: subject, hints: hints, cause: err}
}

// attachNotFoundHints wraps every RunE in the tree so a 404 on its way out picks
// up the hints for the command that produced it.
//
// Done once over the assembled tree rather than at each handleAPIError call
// site: the recovery command is a property of the resource, cobra already hands
// RunE the command that names it, and there are over two hundred of those call
// sites to keep in step otherwise. It also reaches a 404 from a path that never
// called handleAPIError at all.
func attachNotFoundHints(cmd *cobra.Command) {
	for _, sub := range cmd.Commands() {
		attachNotFoundHints(sub)
	}
	inner := cmd.RunE
	if inner == nil {
		return
	}
	cmd.RunE = func(c *cobra.Command, args []string) error {
		return hintNotFound(c, inner(c, args))
	}
}
