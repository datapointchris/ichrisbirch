package cli

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

type eventsListRun struct {
	query  url.Values
	asked  bool
	stdout string
	stderr string
	runErr error
}

func runEventsList(t *testing.T, args ...string) eventsListRun {
	t.Helper()
	var run eventsListRun
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		run.asked = true
		run.query = r.URL.Query()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[]`))
	}))
	t.Cleanup(api.Close)
	asService(t, serviceIDP(t).URL, api.URL, serviceSecret)

	root := NewRootCommand()
	var stdout, stderr bytes.Buffer
	root.SetOut(&stdout)
	root.SetErr(&stderr)
	root.SetArgs(append([]string{"events", "list"}, args...))
	run.runErr = root.Execute()
	run.stdout, run.stderr = stdout.String(), stderr.String()
	return run
}

// Today is this machine's, so the zone goes out beside the scope.
func TestEventsList_AsksForUpcomingInThisMachinesZone(t *testing.T) {
	t.Setenv("TZ", "Asia/Tokyo")

	run := runEventsList(t)

	if run.runErr != nil {
		t.Fatalf("run: %v", run.runErr)
	}
	if got := run.query.Get("when"); got != "upcoming" {
		t.Errorf("sent when=%q, want upcoming", got)
	}
	if got := run.query.Get("timezone"); got != "Asia/Tokyo" {
		t.Errorf("sent timezone=%q, want Asia/Tokyo", got)
	}
	if !strings.Contains(run.stdout, "No upcoming events.") {
		t.Errorf("stdout = %q, want it to say no upcoming events rather than no events", run.stdout)
	}
}

// A narrowed read says so on stderr every time, so a short list explains itself.
func TestEventsList_TheDefaultNamesTheFlagThatShowsThePast(t *testing.T) {
	run := runEventsList(t)

	if !strings.Contains(run.stderr, "icb events list --when all") {
		t.Errorf("stderr = %q, want the command that shows past events", run.stderr)
	}
}

func TestEventsList_AskedForAScopeItSaysNothingHidden(t *testing.T) {
	run := runEventsList(t, "--when", "past")

	if got := run.query.Get("when"); got != "past" {
		t.Errorf("sent when=%q, want past", got)
	}
	if run.stderr != "" {
		t.Errorf("stderr = %q, want silence when the scope was asked for", run.stderr)
	}
}

// The hint is for a person reading the table; --json output stays the data alone.
func TestEventsList_JSONCarriesNoHint(t *testing.T) {
	run := runEventsList(t, "--json")

	if strings.TrimSpace(run.stdout) != "[]" {
		t.Errorf("stdout = %q, want []", run.stdout)
	}
	if run.stderr != "" {
		t.Errorf("stderr = %q, want nothing beside the JSON", run.stderr)
	}
}

func TestEventsList_RefusesAnUnknownScopeBeforeAsking(t *testing.T) {
	run := runEventsList(t, "--when", "soon")

	if run.runErr == nil {
		t.Fatal("--when soon ran; want a usage error")
	}
	if run.asked {
		t.Error("the API was asked; an unknown scope should be refused before the request")
	}
}
