package cli

import (
	"github.com/datapointchris/goselfupdate"
	"github.com/datapointchris/goselfupdate/cobracmd"
	"github.com/spf13/cobra"
)

// newUpdateCommand replaces this binary with the newest published release.
//
// TagPrefix is what makes it resolve the right thing. The CLI is a nested
// module released under cli/v1.2.3 so its tags never collide with the app's,
// and GitHub's "latest release" endpoint is repository-wide — without the
// prefix it would return whatever ichrisbirch released most recently, which is not
// this program.
//
// A locally built binary refuses to update: git describe returns the prefixed
// tag, which is not a semantic version, so it reports as a development build.
// Only CI strips the prefix, so only a released binary can replace itself.
func newUpdateCommand() *cobra.Command {
	return cobracmd.New(goselfupdate.Config{
		Owner:     "datapointchris",
		Repo:      "ichrisbirch",
		Binary:    "icb",
		Version:   version,
		TagPrefix: "cli/",
	})
}
