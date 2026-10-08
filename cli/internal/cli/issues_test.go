package cli

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
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
// extends its own claim rather than being refused.
func TestActorIdentity_NamesTheClaudeCodeSession(t *testing.T) {
	t.Setenv("CLAUDE_CODE_SESSION_ID", "2c3201ae")
	if got := actorIdentity(); got != "claude-code/2c3201ae" {
		t.Errorf("actorIdentity() = %q, want the session", got)
	}
	t.Setenv("CLAUDE_CODE_SESSION_ID", "")
	t.Setenv("USER", "chris")
	if got := actorIdentity(); !strings.HasPrefix(got, "chris") {
		t.Errorf("actorIdentity() = %q outside a session, want the user", got)
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
