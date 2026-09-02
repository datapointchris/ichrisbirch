package cli

import (
	"errors"
	"strings"

	"github.com/spf13/cobra"

	"github.com/datapointchris/goclikit"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// withNotFoundHints records on cmd the commands a 404 under it should name, and
// returns cmd so it can be attached inline in an AddCommand list.
//
// Each hint is a sentence, a colon, and the command to run, matching the
// "Completed tasks are hidden: icb tasks list --status all" line the list
// commands already print when they hide rows.
//
// Local rather than goclikit's own helper so the twenty command files calling
// it import nothing. The annotation is the contract, and its key is exported;
// this file is the only one that has to know whose key it is.
//
// Cobra does not inherit annotations and the lookup takes the nearest ancestor
// carrying them, so a subcommand acting on a second kind of id names every way
// in: `complete-task` takes an item and a task, and lists both.
func withNotFoundHints(cmd *cobra.Command, hints ...string) *cobra.Command {
	if cmd.Annotations == nil {
		cmd.Annotations = map[string]string{}
	}
	cmd.Annotations[goclikit.RecoveryHintsAnnotation] = strings.Join(hints, "\n")
	return cmd
}

// notFound reports whether err is the API saying a resource is not there, and
// the line naming which one.
//
// The subject is the API's, not one built from the arguments, because only the
// API knows which id was missing: `icb projects items complete-task 598 4` can
// 404 on either number and the message names the one that did.
//
// The "API request failed (404 Not Found)" prefix goes with it. That reports how
// the answer arrived, and a 404 is an answer rather than a failure to get one.
//
// An empty Message is the case where it is not: a proxy error page or an
// Authelia redirect decodes to a status and nothing else, and the resource was
// never reached. Reporting no subject leaves the status line alone rather than
// replacing it with a resource claim nothing established.
func notFound(err error) (string, bool) {
	var apiErr *api.APIError
	if !errors.As(err, &apiErr) || !apiErr.NotFound() {
		return "", false
	}
	return apiErr.Message, true
}
