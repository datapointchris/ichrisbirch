package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// Every refusal that needs no server state is decided before the client
// exists, so it exits 2 even with the API unreachable.
func TestIssues_AUsageRefusalDoesNotWaitOnTheNetwork(t *testing.T) {
	cases := []struct {
		name string
		args []string
	}{
		{"a queue flag beside a named issue", []string{"issues", "claim", "412", "--repo", "ichrisbirch"}},
		{"a claim shorter than a minute", []string{"issues", "claim", "--minutes", "0"}},
		{"a claim with no claimant", []string{"issues", "claim", "--claimant", ""}},
		{"a cancel with no reason", []string{"issues", "cancel", "412"}},
		{"an edit changing nothing", []string{"issues", "edit", "412"}},
		{"emptying the title", []string{"issues", "edit", "412", "--title", ""}},
		{"a label beside an empty one", []string{"issues", "edit", "412", "--label", "area-api", "--label", ""}},
		{"a deferral that is not a day", []string{"issues", "edit", "412", "--deferred-until", "tomorrow"}},
		{"an unknown type", []string{"issues", "edit", "412", "--type", "epic"}},
		{"a title missing with no terminal", []string{"issues", "create", "--no-input"}},
		{"a new issue already closed", []string{"issues", "create", "--title", "x", "--status", "completed"}},
		{"an unknown status", []string{"issues", "list", "--status", "done"}},
		{"an unknown priority", []string{"issues", "list", "--priority", "extreme"}},
		{"a reorder with no neighbor", []string{"issues", "reorder", "412"}},
		{"a reorder with both neighbors", []string{"issues", "reorder", "412", "--before", "1", "--after", "2"}},
		{"a negative tree depth", []string{"issues", "tree", "--depth", "-1"}},
		{"an initiative dropped with no reason", []string{"issues", "initiatives", "drop", "Ship it"}},
		{"a label edit changing nothing", []string{"issues", "labels", "edit", "area-api"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			unreachableAPI(t)
			if code := runTree(t, tc.args...); code != 2 {
				t.Errorf("exit code = %d, want 2", code)
			}
		})
	}
}

func parsedEdit(t *testing.T, args ...string) (*issueEditFlags, *cobra.Command) {
	t.Helper()
	v := &issueEditFlags{}
	cmd := &cobra.Command{}
	v.register(cmd)
	if err := cmd.ParseFlags(args); err != nil {
		t.Fatalf("ParseFlags(%v): %v", args, err)
	}
	return v, cmd
}

// An empty --deferred-until or --initiative goes out as a null. An empty
// --label goes out as an empty list, because the API answers a null labels
// with 422.
func TestIssueEdit_EmptyValuesClearEachFieldItsOwnWay(t *testing.T) {
	v, cmd := parsedEdit(t, "--deferred-until", "", "--initiative", "", "--label", "", "--priority", "none")
	in, clear, err := v.update(cmd)
	if err != nil {
		t.Fatalf("update: %v", err)
	}
	if strings.Join(clear, ",") != "deferred_until_date,initiative" {
		t.Errorf("clear = %v, want the deferral and the initiative", clear)
	}
	if in.Labels == nil || len(*in.Labels) != 0 {
		t.Errorf("labels = %v, want an empty list", in.Labels)
	}
	if in.Priority == nil || *in.Priority != 0 {
		t.Errorf("priority = %v, want 0 for none", in.Priority)
	}
	if in.DeferredUntilDate != nil || in.Initiative != nil {
		t.Errorf("a cleared field also went in the body: %+v", in)
	}
}

// Two sessions on one machine must not share a claimant, because a claimant
// extends its own claim rather than being refused. The prefix is the kind of
// actor, which is what a reader filters a person's work from a worker's by.
func TestActorIdentity_NamesTheKindOfActorBeforeWhoItIs(t *testing.T) {
	cases := []struct {
		name, session, attended, worker, want string
	}{
		{"a session someone attends", "2c3201ae", "1", "", "claude-code/2c3201ae"},
		{"an older session that does not say", "2c3201ae", "", "", "claude-code/2c3201ae"},
		{"a session nobody attends", "2c3201ae", "0", "", "claude-code-unattended/2c3201ae"},
		{"a session a named worker started", "2c3201ae", "0", "fix@scheduler", "claude-code-unattended/fix@scheduler/2c3201ae"},
		{"a named worker running icb itself", "", "", "runner-update@scheduler", "worker/runner-update@scheduler"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			t.Setenv("CLAUDE_CODE_SESSION_ID", c.session)
			t.Setenv("CLAUDE_CODE_SESSION_ATTENDED", c.attended)
			t.Setenv(actorWorkerEnv, c.worker)
			if got := actorIdentity(); got != c.want {
				t.Errorf("actorIdentity() = %q, want %q", got, c.want)
			}
		})
	}
}

func TestActorIdentity_IsThePersonOutsideASessionOrAWorker(t *testing.T) {
	t.Setenv("CLAUDE_CODE_SESSION_ID", "")
	t.Setenv(actorWorkerEnv, "")
	t.Setenv("USER", "chris")
	if got := actorIdentity(); !strings.HasPrefix(got, "chris") {
		t.Errorf("actorIdentity() = %q outside a session, want the user", got)
	}
}

// A Claude Code session closing an issue: the PATCH names the session unless
// --closed-by names someone else or is emptied.
func TestIssues_CompleteAndCancelSendWhoIsClosingInTheirPatch(t *testing.T) {
	t.Setenv("CLAUDE_CODE_SESSION_ID", "2c3201ae")
	t.Setenv("CLAUDE_CODE_SESSION_ATTENDED", "1")
	t.Setenv(actorWorkerEnv, "")
	idp := serviceIDP(t)
	verbs := [][]string{{"issues", "complete", "412"}, {"issues", "cancel", "412", "--reason", "superseded"}}
	cases := []struct {
		flags []string
		want  *string
	}{
		{nil, ptr("claude-code/2c3201ae")},
		{[]string{"--closed-by", "chris@desk"}, ptr("chris@desk")},
		{[]string{"--closed-by", ""}, nil},
	}
	for _, verb := range verbs {
		for _, c := range cases {
			args := append(slices.Clone(verb), c.flags...)
			t.Run(strings.Join(args, " "), func(t *testing.T) {
				var patch map[string]any
				api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					if r.Method == http.MethodPatch {
						_ = json.NewDecoder(r.Body).Decode(&patch)
					}
					w.Header().Set("Content-Type", "application/json")
					_, _ = w.Write([]byte(`{"id":"019a2b3c-4d5e-7f60-8a9b-0c1d2e3f4a5b","number":412,"title":"t","status":"open"}`))
				}))
				t.Cleanup(api.Close)
				asService(t, idp.URL, api.URL, serviceSecret)

				if _, err := runService(t, args...); err != nil {
					t.Fatalf("run: %v", err)
				}
				if patch == nil {
					t.Fatal("sent no PATCH")
				}
				got, sent := patch["closed_by"]
				switch {
				case c.want == nil && sent:
					t.Errorf("sent closed_by %v, want it left out", got)
				case c.want != nil && got != *c.want:
					t.Errorf("sent closed_by %v, want %q", got, *c.want)
				}
			})
		}
	}
}

// Reading what attended sessions finished: --closed-by reaches the API as the
// prefix it matches on.
func TestIssues_ListClosedBySendsThePrefixToMatch(t *testing.T) {
	var query url.Values
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		query = r.URL.Query()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[]`))
	}))
	t.Cleanup(api.Close)
	asService(t, serviceIDP(t).URL, api.URL, serviceSecret)

	if _, err := runService(t, "issues", "list", "--status", "completed", "--closed-by", "claude-code/", "--json"); err != nil {
		t.Fatalf("run: %v", err)
	}
	if got := query.Get("closed_by"); got != "claude-code/" {
		t.Errorf("sent closed_by %q, want claude-code/", got)
	}
}

func TestClosedNote_SaysWhenAndWhoWhereEachIsKnown(t *testing.T) {
	now := time.Date(2026, 10, 7, 12, 0, 0, 0, time.Local)
	closed := now.Add(-time.Hour)
	who := "claude-code/2c3201ae"
	cases := []struct {
		name  string
		issue api.Issue
		want  string
	}{
		{"open", api.Issue{}, ""},
		{"closed by a known actor", api.Issue{ClosedTS: &closed, ClosedBy: &who}, "11:00 by claude-code/2c3201ae"},
		{"closed before anyone was recorded", api.Issue{ClosedTS: &closed}, "11:00"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := closedNote(c.issue, now); got != c.want {
				t.Errorf("closedNote() = %q, want %q", got, c.want)
			}
		})
	}
}

func TestIssueStateNotes_SayWhyAnIssueWaits(t *testing.T) {
	now := time.Date(2026, 10, 7, 12, 0, 0, 0, time.Local)
	later := now.Add(2 * time.Hour)
	tomorrow := now.AddDate(0, 0, 1).Format(dayLayout)
	yesterday := now.AddDate(0, 0, -1).Format(dayLayout)
	claimant := "claude-code/abc"
	issue := api.Issue{
		Status:            api.IssueStatusInProgress,
		ClaimedBy:         &claimant,
		ClaimExpiresTS:    &later,
		DeferredUntilDate: &tomorrow,
		DependsOn: []api.IssueSummary{
			{Number: 411, Status: api.IssueStatusOpen},
			{Number: 400, Status: api.IssueStatusCompleted},
		},
		OpenChildCount: 1,
	}
	want := "claimed by claude-code/abc until 14:00; blocked by #411; deferred until " + tomorrow + "; 1 open child"
	if got := strings.Join(issueStateNotes(issue, now), "; "); got != want {
		t.Errorf("notes = %q\nwant    %q", got, want)
	}

	issue.DeferredUntilDate = &yesterday
	issue.ClaimExpiresTS = ptr(now.Add(-time.Minute))
	issue.DependsOn = nil
	issue.OpenChildCount = 0
	if got := strings.Join(issueStateNotes(issue, now), "; "); got != "claim by claude-code/abc expired" {
		t.Errorf("notes = %q, want only the expired claim", got)
	}

	issue.Status = api.IssueStatusCompleted
	if notes := issueStateNotes(issue, now); len(notes) != 0 {
		t.Errorf("a closed issue carried notes %v", notes)
	}
}

func TestPriorityCell_StarsAnInheritedPriority(t *testing.T) {
	if got := priorityCell(api.Issue{Priority: 0, EffectivePriority: 2}); got != "high*" {
		t.Errorf("inherited = %q, want high*", got)
	}
	if got := priorityCell(api.Issue{Priority: 0, EffectivePriority: 0}); got != "none" {
		t.Errorf("none = %q, want none", got)
	}
}

func TestReinvocation_KeepsTheFiltersItWidens(t *testing.T) {
	cmd := findCommand(t, "issues", "list")
	if err := cmd.ParseFlags([]string{"--repo", "", "--blocked=false", "--label", "area-cli", "--json"}); err != nil {
		t.Fatalf("ParseFlags: %v", err)
	}
	want := "icb issues list --blocked=false --label area-cli --repo '' --status all"
	if got := reinvocation(cmd, "--status all"); got != want {
		t.Errorf("reinvocation = %q\nwant          %q", got, want)
	}
}

func TestResolveIssueComment_ByPlaceOrById(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[
			{"id":"019a0000-0000-7000-8000-00000000000a","issue_id":"i","body":"first","created_ts":"2026-10-07T12:00:00Z"},
			{"id":"019a0000-0000-7000-8000-00000000000b","issue_id":"i","body":"second","created_ts":"2026-10-07T12:00:00Z"}
		]`))
	}))
	t.Cleanup(srv.Close)
	client := api.New(srv.URL, srv.Client())
	ctx := context.Background()

	for ref, want := range map[string]string{"2": "second", "#1": "first", "019a0000-0000-7000-8000-00000000000b": "second"} {
		comment, err := resolveIssueComment(ctx, client, "412", ref)
		if err != nil || comment.Body != want {
			t.Errorf("resolve %q = %q, %v; want %q", ref, comment.Body, err, want)
		}
	}
	if _, err := resolveIssueComment(ctx, client, "412", "3"); err == nil || !strings.Contains(err.Error(), "no #3") {
		t.Errorf("resolve 3 = %v, want it to say there is no #3", err)
	}
}

func TestIssueTrees_HideFinishedWorkByDefault(t *testing.T) {
	byID := map[string]api.Issue{
		"a": {ID: "a", Status: api.IssueStatusCompleted},
		"b": {ID: "b", Status: api.IssueStatusCanceled},
		"c": {ID: "c", Status: api.IssueStatusOpen},
	}
	if issueComponentMatches([]string{"a", "b"}, byID, "", nil) {
		t.Error("a finished tree was kept by default")
	}
	if !issueComponentMatches([]string{"a", "c"}, byID, "", nil) {
		t.Error("a tree with open work was hidden")
	}
	if !issueComponentMatches([]string{"a", "b"}, byID, api.IssueStatusAll, nil) {
		t.Error("--status all hid a finished tree")
	}
}

func TestPrintIssuesTable_LeadsWithTheNumberAndShowsWhyItWaits(t *testing.T) {
	var out bytes.Buffer
	printIssuesTable(&out, []api.Issue{{
		Number: 412, Title: "Route the new paths", Type: "bug", Status: api.IssueStatusOpen,
		EffectivePriority: 2, DependsOn: []api.IssueSummary{{Number: 411, Status: api.IssueStatusOpen}},
	}}, time.Now())
	row := lineContaining(t, out.String(), "Route the new paths")
	if !strings.HasPrefix(row, "412 ") || !strings.Contains(row, "[blocked by #411]") || !strings.Contains(row, "high*") {
		t.Errorf("row = %q", row)
	}
}
