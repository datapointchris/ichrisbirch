package cli

import (
	"strings"

	"github.com/spf13/cobra"
)

// usePad sizes the command column from the full `Use` string rather than the
// bare command name. Cobra's default lists `complete`; this lists
// `complete <project>`, so the arguments a verb takes are readable from the
// parent screen instead of one drill-down away.
//
// That matters here because the Use strings already carry their arguments —
// `drop <project> --reason <why>`, `create --name <name> [flags]` — and cobra
// was discarding all of it when rendering the list.
func usePad(cmds []*cobra.Command) int {
	width := 0
	for _, c := range cmds {
		if !c.IsAvailableCommand() && c.Name() != "help" {
			continue
		}
		if n := len(c.Use); n > width {
			width = n
		}
	}
	// +1 so the longest row still gets a two-space gutter. Cobra's own padding
	// leaves it with one.
	return width + 1
}

// usageTemplate is the stock cobra template with the three command-list rows
// rewritten to use `Use` and the computed width. Everything else is cobra's
// own, so an upgrade that changes the surrounding structure shows up as a
// visible diff rather than a silent divergence.
const usageTemplate = `Usage:{{if .Runnable}}
  {{.UseLine}}{{end}}{{if .HasAvailableSubCommands}}
  {{.CommandPath}} [command]{{end}}{{if gt (len .Aliases) 0}}

Aliases:
  {{.NameAndAliases}}{{end}}{{if .HasExample}}

Examples:
{{.Example}}{{end}}{{if .HasAvailableSubCommands}}{{$cmds := .Commands}}{{$pad := usePad .Commands}}{{if eq (len .Groups) 0}}

Available Commands:{{range $cmds}}{{if (or .IsAvailableCommand (eq .Name "help"))}}
  {{rpad .Use $pad}} {{.Short}}{{end}}{{end}}{{else}}{{range $group := .Groups}}

{{.Title}}{{range $cmds}}{{if (and (eq .GroupID $group.ID) (or .IsAvailableCommand (eq .Name "help")))}}
  {{rpad .Use $pad}} {{.Short}}{{end}}{{end}}{{end}}{{if not .AllChildCommandsHaveGroup}}

Additional Commands:{{range $cmds}}{{if (and (eq .GroupID "") (or .IsAvailableCommand (eq .Name "help")))}}
  {{rpad .Use $pad}} {{.Short}}{{end}}{{end}}{{end}}{{end}}{{end}}{{if .HasAvailableLocalFlags}}

Flags:
{{.LocalFlags.FlagUsages | trimTrailingWhitespaces}}{{end}}{{if .HasAvailableInheritedFlags}}

Global Flags:
{{.InheritedFlags.FlagUsages | trimTrailingWhitespaces}}{{end}}{{if .HasHelpSubCommands}}

Additional help topics:{{range .Commands}}{{if .IsAdditionalHelpTopicCommand}}
  {{rpad .CommandPath .CommandPathPadding}} {{.Short}}{{end}}{{end}}{{end}}{{if .HasAvailableSubCommands}}

Use "{{.CommandPath}} [command] --help" for more information about a command.{{end}}
`

func init() {
	cobra.AddTemplateFunc("usePad", usePad)
}

// applyUsageTemplate installs the template on a command and everything under
// it. Cobra inherits a usage template from the parent only for commands added
// before it is set, and the tree is assembled with AddCommand after the root
// exists, so this walks instead.
func applyUsageTemplate(cmd *cobra.Command) {
	cmd.SetUsageTemplate(strings.TrimPrefix(usageTemplate, "\n"))
	for _, c := range cmd.Commands() {
		applyUsageTemplate(c)
	}
}
