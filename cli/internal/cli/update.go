package cli

import (
	"os"
	"os/exec"
	"strings"

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
		Token:     githubToken(),
	})
}

// githubToken resolves a GitHub credential the way the dotfiles installer does:
// the environment first, then the gh CLI's stored token.
//
// goselfupdate reads $GITHUB_TOKEN and $GH_TOKEN on its own, so this only adds
// the third source. It is needed rather than optional — the releases live in a
// private repository, and the API answers an unauthenticated request with a 404
// that reads as "no release" rather than "no permission". On a public
// repository it still earns its place by lifting the 60-requests-per-hour
// unauthenticated rate limit.
func githubToken() string {
	for _, name := range []string{"GITHUB_TOKEN", "GH_TOKEN"} {
		if token := os.Getenv(name); token != "" {
			return token
		}
	}
	out, err := exec.Command("gh", "auth", "token").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}
