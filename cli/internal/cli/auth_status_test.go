package cli

import (
	"bytes"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"testing"

	"github.com/spf13/cobra"
	"golang.org/x/oauth2"
)

func statusOutput(r statusReport) string {
	cmd := &cobra.Command{}
	var out bytes.Buffer
	cmd.SetOut(&out)
	cmd.SetErr(&bytes.Buffer{})
	printStatus(cmd, r)
	return out.String()
}

func TestClassifySession_UsableTokenIsLive(t *testing.T) {
	token := &oauth2.Token{AccessToken: "at-1"}
	state, got := classifySession(token, nil)
	if state != sessionLive {
		t.Errorf("session = %q, want %q", state, sessionLive)
	}
	if got != token {
		t.Error("the usable token was not returned")
	}
}

// This is the state the old message called "expired — will refresh on next use".
// The issuer has dropped the grant, and only a login brings it back.
func TestClassifySession_RefusedRefreshIsRejected(t *testing.T) {
	retrieveErr := &oauth2.RetrieveError{
		Response:  &http.Response{StatusCode: http.StatusBadRequest},
		Body:      []byte(`{"error":"invalid_grant"}`),
		ErrorCode: "invalid_grant",
	}
	wrapped := &url.Error{Op: "Post", URL: "https://auth.example.com/token", Err: retrieveErr}
	if state, _ := classifySession(nil, wrapped); state != sessionRejected {
		t.Errorf("session = %q, want %q", state, sessionRejected)
	}
}

// An issuer this machine cannot reach proves nothing about the grant, so the
// report says so rather than picking one of the other two answers.
func TestClassifySession_UnreachableIssuerIsUnverified(t *testing.T) {
	err := fmt.Errorf("reach identity provider: %w", errors.New("connection refused"))
	if state, _ := classifySession(nil, err); state != sessionUnverified {
		t.Errorf("session = %q, want %q", state, sessionUnverified)
	}
}

func TestPrintStatus_RejectedNamesTheLoginCommand(t *testing.T) {
	got := statusOutput(statusReport{
		LoggedIn: true,
		ClientID: "icb-cli-archlinux",
		Issuer:   "https://auth.example.com",
		Session:  sessionRejected,
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
		Session:   sessionLive,
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
		Session:   sessionUnverified,
	})
	if !strings.Contains(got, "unverified") {
		t.Errorf("got %q, want the unverified state stated", got)
	}
}
