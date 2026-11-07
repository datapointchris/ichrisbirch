package cli

import (
	"os"
	"os/exec"
	"strings"

	"github.com/datapointchris/goclikit"
	"github.com/datapointchris/goselfupdate"
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
func updateConfig() goselfupdate.Config {
	return goselfupdate.Config{
		Owner:     "datapointchris",
		Repo:      "ichrisbirch",
		Binary:    "icb",
		Version:   version,
		TagPrefix: "cli/",
		// Lazy: Execute builds this config on every invocation, and an eager
		// githubToken() would run `gh auth token` before every command, even
		// when the daily update check is skipped.
		TokenFunc: githubToken,
	}
}

func newUpdateCommand() *cobra.Command {
	return goclikit.UpdateCommand(updateConfig())
}

// githubToken resolves a GitHub credential: the environment first, then the gh
// CLI's stored token. goselfupdate reads $GITHUB_TOKEN and $GH_TOKEN itself, so
// this adds the gh fallback, which lifts the 60-requests-per-hour
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
