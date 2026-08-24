package cli

import (
	"bytes"
	"strings"
	"testing"

	"github.com/datapointchris/goclilogin"
	"github.com/spf13/cobra"
)

// Classifying a session lives in goclilogin, which tests it against a provider
// that rotates and revokes. What is icb's own is how each of the three states
// reads on the terminal.
func statusOutput(r statusReport) string {
	cmd := &cobra.Command{}
	var out bytes.Buffer
	cmd.SetOut(&out)
	cmd.SetErr(&bytes.Buffer{})
	printStatus(cmd, r)
	return out.String()
}

func TestPrintStatus_NotLoggedInNamesTheLoginCommand(t *testing.T) {
	got := statusOutput(statusReport{ClientID: "icb-cli-archlinux"})
	if !strings.Contains(got, "icb auth login") {
		t.Errorf("got %q, want the login command named", got)
	}
}

func TestPrintStatus_RejectedNamesTheLoginCommand(t *testing.T) {
	got := statusOutput(statusReport{
		LoggedIn: true,
		ClientID: "icb-cli-archlinux",
		Issuer:   "https://auth.example.com",
		Session:  goclilogin.SessionRejected,
	})
	if !strings.Contains(got, "icb auth login") {
		t.Errorf("got %q, want the login command named", got)
	}
	if !strings.Contains(got, "rejected") {
		t.Errorf("got %q, want the rejection stated", got)
	}
}

// The promise this used to make is the defect: an expired access token behind a
// revoked grant never refreshes, and the CLI cannot tell which it has until it
// asks.
func TestPrintStatus_ExpiredDoesNotPromiseARefresh(t *testing.T) {
	got := statusOutput(statusReport{
		LoggedIn:  true,
		ClientID:  "icb-cli-archlinux",
		Issuer:    "https://auth.example.com",
		ExpiresAt: "2026-08-22T06:13:47-04:00",
		Expired:   true,
		Session:   goclilogin.SessionLive,
	})
	if strings.Contains(got, "will refresh") {
		t.Errorf("got %q, want no promise the CLI cannot keep", got)
	}
}

func TestPrintStatus_UnverifiedSaysWhyItCouldNotAnswer(t *testing.T) {
	got := statusOutput(statusReport{
		LoggedIn:  true,
		ClientID:  "icb-cli-archlinux",
		Issuer:    "https://auth.example.com",
		ExpiresAt: "2026-08-22T06:13:47-04:00",
		Expired:   true,
		Session:   goclilogin.SessionUnverified,
	})
	if !strings.Contains(got, "unverified") {
		t.Errorf("got %q, want the unverified state stated", got)
	}
}
