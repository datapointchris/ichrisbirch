package cli

import (
	"fmt"
	"io"
	"os"
	"slices"
	"strconv"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

// issueHints are the ways to find a valid issue number after a 404.
var issueHints = []string{
	"Search issues by title or description: icb issues search <query>",
	"Completed and canceled issues are hidden: icb issues list --status all",
}

// issueNumberHints go on every verb taking an issue number, for the reason
// itemNumberHints gives.
var issueNumberHints = append(slices.Clone(issueHints),
	"Project items share issue numbers, so the number may name an item: icb projects items show <number>")

// defaultNextIssueLimit caps `next`. The head of the queue is the answer, and
// the rows after it are context.
const defaultNextIssueLimit = 10

const (
	issueGroupRead      = "read"
	issueGroupWork      = "work"
	issueGroupFile      = "file"
	issueGroupLifecycle = "lifecycle"
	issueGroupOrder     = "order"
	issueGroupGrouping  = "grouping"
)

func newIssuesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use: "issues",
		// Top-level words that mean an issue: `items`, or a verb typed with no noun.
		SuggestFor: []string{"items", "show", "search"},
		Short:      "Track development work: bugs, features, chores, and the decisions they wait on",
		Long: "Development work, mostly filed and taken by agents. An issue needs no project:\n" +
			"its repo, labels and dependencies place it, and an optional initiative groups\n" +
			"the issues that ship together. Personal projects stay in `icb projects`.\n" +
			"\n" +
			"An issue is ready when it is open or its claim has run out, everything it\n" +
			"depends on is closed, its deferral day has come, and none of its children is\n" +
			"still open. `next` lists the ready issues in the order to take them: priority\n" +
			"first, then rank. A blocker takes the most urgent priority of what it blocks,\n" +
			"and an issue with no priority of its own takes its parent's or its\n" +
			"initiative's.\n" +
			"\n" +
			"`claim` takes the head of that queue, or a named issue, until the claim runs\n" +
			"out. Decisions wait on a person, so the queue leaves them out.\n" +
			"`icb issues list --type decision` lists them.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd, issueHints...)
	cmd.AddGroup(
		&cobra.Group{ID: issueGroupRead, Title: "Reading:"},
		&cobra.Group{ID: issueGroupWork, Title: "Taking work:"},
		&cobra.Group{ID: issueGroupFile, Title: "Filing:"},
		&cobra.Group{ID: issueGroupLifecycle, Title: "Lifecycle:"},
		&cobra.Group{ID: issueGroupOrder, Title: "Order and dependencies:"},
		&cobra.Group{ID: issueGroupGrouping, Title: "Grouping:"},
	)
	add := func(group string, commands ...*cobra.Command) {
		for _, c := range commands {
			c.GroupID = group
			cmd.AddCommand(c)
		}
	}
	add(issueGroupRead,
		newIssuesListCommand(),
		newIssuesSearchCommand(),
		withNotFoundHints(newIssuesShowCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesCommentsCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesTreeCommand(), issueNumberHints...),
		newIssuesVocabularyCommand(),
	)
	add(issueGroupWork,
		newIssuesNextCommand(),
		withNotFoundHints(newIssuesClaimCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesReleaseCommand(), issueNumberHints...),
	)
	add(issueGroupFile,
		withNotFoundHints(newIssuesCreateCommand(), append(slices.Clone(issueHints), initiativeHints...)...),
		withNotFoundHints(newIssuesEditCommand(), append(slices.Clone(issueNumberHints), initiativeHints...)...),
		withNotFoundHints(newIssuesAddCommentCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesRemoveCommentCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesDeleteCommand(), issueNumberHints...),
	)
	add(issueGroupLifecycle,
		withNotFoundHints(newIssuesAcceptCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesCompleteCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesCancelCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesReopenCommand(), issueNumberHints...),
	)
	add(issueGroupOrder,
		withNotFoundHints(newIssuesReorderCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesAddDependencyCommand(), issueNumberHints...),
		withNotFoundHints(newIssuesRemoveDependencyCommand(), issueNumberHints...),
	)
	add(issueGroupGrouping,
		newIssueInitiativesCommand(),
		newIssueLabelsCommand(),
	)
	return cmd
}

// --- Filters shared by list and search ---

// issueFilterFlags are the questions a list of issues answers, declared once
// so list and search ask them the same way.
type issueFilterFlags struct {
	status     string
	repo       string
	issueType  string
	label      string
	initiative string
	parent     string
	priority   string
	claimedBy  string
	blocked    bool
}

func (v *issueFilterFlags) register(cmd *cobra.Command, statusDefault string) {
	f := cmd.Flags()
	f.StringVar(&v.status, "status", "", "One of: "+strings.Join(api.IssueStatuses, ", ")+" (default "+statusDefault+")")
	f.StringVar(&v.repo, "repo", "", "Only issues on this repo (empty string for issues on no repo)")
	f.StringVar(&v.issueType, "type", "", "One of: "+strings.Join(api.IssueTypes, ", "))
	f.StringVar(&v.label, "label", "", "Only issues carrying this label (see: icb issues labels list)")
	f.StringVar(&v.initiative, "initiative", "", "Only issues in this initiative, by name or id")
	f.StringVar(&v.parent, "parent", "", "Only the children of this issue")
	f.StringVar(&v.priority, "priority", "", "Only issues whose own priority is this: "+priorityChoices())
	f.StringVar(&v.claimedBy, "claimed-by", "", "Only issues held by this claimant")
	f.BoolVar(&v.blocked, "blocked", false, "Only issues waiting on an unclosed dependency (--blocked=false for the rest)")
}

// filter validates what can be refused without the API and builds the query.
func (v *issueFilterFlags) filter(cmd *cobra.Command) (api.IssueFilter, error) {
	f := cmd.Flags()
	if f.Changed("status") && !slices.Contains(api.IssueStatuses, v.status) {
		return api.IssueFilter{}, usageError{fmt.Errorf("unknown status %q — one of: %s", v.status, strings.Join(api.IssueStatuses, ", "))}
	}
	if err := validateIssueType(f, "type", v.issueType); err != nil {
		return api.IssueFilter{}, err
	}
	filter := api.IssueFilter{
		Status:     v.status,
		Repo:       repoFlagValue(cmd, v.repo),
		Type:       v.issueType,
		Label:      v.label,
		Initiative: v.initiative,
		Parent:     v.parent,
		ClaimedBy:  v.claimedBy,
	}
	if f.Changed("priority") {
		priority, err := parsePriority(v.priority)
		if err != nil {
			return api.IssueFilter{}, usageError{fmt.Errorf("--priority: %w", err)}
		}
		filter.Priority = &priority
	}
	if f.Changed("blocked") {
		filter.Blocked = &v.blocked
	}
	return filter, nil
}

func validateIssueType(f *pflag.FlagSet, name, value string) error {
	if !f.Changed(name) || slices.Contains(api.IssueTypes, value) {
		return nil
	}
	return usageError{fmt.Errorf("unknown type %q — one of: %s", value, strings.Join(api.IssueTypes, ", "))}
}

// parsePriority reads a priority by name or by value, so `--priority high` and
// `--priority 2` are the same filter.
func parsePriority(raw string) (int, error) {
	if n, err := strconv.Atoi(raw); err == nil && n >= 0 && n < len(api.IssuePriorityNames) {
		return n, nil
	}
	for value, name := range api.IssuePriorityNames {
		if strings.EqualFold(strings.TrimSpace(raw), name) {
			return value, nil
		}
	}
	return 0, fmt.Errorf("unknown priority %q — one of: %s", raw, priorityChoices())
}

func priorityChoices() string {
	return strings.Join(api.IssuePriorityNames, ", ") + " (or 0-4)"
}

func priorityName(value int) string {
	if value < 0 || value >= len(api.IssuePriorityNames) {
		return strconv.Itoa(value)
	}
	return api.IssuePriorityNames[value]
}

// issueZone is the calendar a deferral day is read in, which is this machine's.
func issueZone() api.DayZone { return api.DayZone(LocalZoneName()) }

// --- Reads over collections ---

func newIssuesListCommand() *cobra.Command {
	var (
		asJSON  bool
		filters issueFilterFlags
		start   string
		end     string
		limit   int
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List issues, open work first in queue order",
		Long: "Unclosed issues by default: triage, open and in progress. Completed and\n" +
			"canceled ones accumulate without end, so --status asks for them.\n" +
			"\n" +
			"Open work comes first in the order `next` takes it, then closed work, latest\n" +
			"first. The priority column is the one the queue sorts by, and a * marks one\n" +
			"inherited from what the issue blocks, its parent, or its initiative. --priority\n" +
			"filters on an issue's own.\n" +
			"\n" +
			"--start/--end bound when an issue closed, inclusive, read in this machine's\n" +
			"zone. Pair them with --status completed to read a week's finished work.",
		Example: "  icb issues list\n" +
			"  icb issues list --repo ichrisbirch\n" +
			"  icb issues list --type decision\n" +
			"  icb issues list --status triage\n" +
			"  icb issues list --blocked\n" +
			"  icb issues list --label area-cli --priority high\n" +
			"  icb issues list --status completed --start 2026-10-01 --json",
		Args: noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			filter, err := filters.filter(cmd)
			if err != nil {
				return err
			}
			hidClosed := !cmd.Flags().Changed("status")
			return runIssuesCollection(cmd, asJSON, hidClosed, func(c *api.Client) ([]api.Issue, error) {
				return c.ListIssues(cmd.Context(), filter, api.OnOrAfter(start), api.OnOrBefore(end), issueZone(), limitFlag(cmd))
			})
		},
	}
	filters.register(cmd, "unclosed")
	cmd.Flags().StringVar(&start, "start", "", "Only issues closed on or after this ISO 8601 date")
	cmd.Flags().StringVar(&end, "end", "", "Only issues closed on or before this ISO 8601 date")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output issues as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newIssuesSearchCommand() *cobra.Command {
	var (
		asJSON  bool
		filters issueFilterFlags
		limit   int
	)
	cmd := &cobra.Command{
		Use:   "search <query>",
		Short: "Find issues by title or description, closed ones included",
		Long: "Searches every status unless --status narrows it, because the issue you\n" +
			"remember may be the one that was finished or canceled.",
		Example: "  icb issues search \"rank renumber\"\n" +
			"  icb issues search routing --repo ichrisbirch --status open",
		Args: usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			filter, err := filters.filter(cmd)
			if err != nil {
				return err
			}
			if filter.Status == "" {
				filter.Status = api.IssueStatusAll
			}
			filter.Search = args[0]
			return runIssuesCollection(cmd, asJSON, false, func(c *api.Client) ([]api.Issue, error) {
				return c.ListIssues(cmd.Context(), filter, "", "", issueZone(), limitFlag(cmd))
			})
		},
	}
	filters.register(cmd, "all")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output issues as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

// runIssuesCollection renders a read returning issues as JSON or a table. When
// hidClosed, the read took the default that leaves closed issues out, and says
// so on stderr with the command that widens it.
func runIssuesCollection(cmd *cobra.Command, asJSON, hidClosed bool, read func(*api.Client) ([]api.Issue, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	issues, err := read(client)
	if err != nil {
		return handleArgumentAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), issues)
	}
	printIssuesTable(cmd.OutOrStdout(), issues, time.Now())
	if hidClosed {
		_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "\nCompleted and canceled issues are hidden: %s\n", reinvocation(cmd, "--status all"))
	}
	return nil
}

// reinvocation is the command that was run, flags and all, with extra added: a
// hint that widens a filtered read must keep the filters it widens.
func reinvocation(cmd *cobra.Command, extra string) string {
	parts := []string{cmd.CommandPath()}
	for _, arg := range cmd.Flags().Args() {
		parts = append(parts, shellQuote(arg))
	}
	cmd.Flags().Visit(func(flag *pflag.Flag) {
		if flag.Name == "json" {
			return
		}
		if flag.Value.Type() == "bool" {
			if flag.Value.String() == "true" {
				parts = append(parts, "--"+flag.Name)
			} else {
				parts = append(parts, "--"+flag.Name+"=false")
			}
			return
		}
		for _, value := range rawFlagValues(flag) {
			parts = append(parts, "--"+flag.Name, shellQuote(value))
		}
	})
	return strings.Join(append(parts, extra), " ")
}

func newIssuesNextCommand() *cobra.Command {
	var (
		asJSON bool
		queue  readyQueueFlags
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "next",
		Short: "The ready issues, in the order to take them",
		Long: "Open, unblocked, not deferred past today, with no open children, and not held\n" +
			"by a live claim. The first row is what `icb issues claim` with no issue would\n" +
			"take, under the same flags. Decisions wait on a person and are left out unless\n" +
			"--type decision asks for them.",
		Example: "  icb issues next\n" +
			"  icb issues next --repo ichrisbirch --limit 1\n" +
			"  icb issues next --label area-cli --json\n" +
			"  icb issues next --type decision",
		Args: noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			filter, err := queue.filter(cmd)
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			// Uncapped, so an empty queue is told apart from --limit 0 below.
			ready, err := client.ListReadyIssues(cmd.Context(), filter, issueZone(), nil)
			if err != nil {
				return handleArgumentAPIError(err)
			}
			shown := ready[:min(limit, len(ready))]
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), shown)
			}
			if len(ready) == 0 {
				_, _ = fmt.Fprintln(cmd.OutOrStdout(), "No issue is ready.")
				return nil
			}
			if len(shown) > 0 {
				printIssuesTable(cmd.OutOrStdout(), shown, time.Now())
			}
			return nil
		},
	}
	queue.register(cmd)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output issues as JSON to stdout")
	addCapFlag(cmd, &limit, defaultNextIssueLimit, "Maximum number of issues to show")
	return cmd
}

// readyQueueFlags narrow the ready queue, on `next` and on `claim` with no issue.
type readyQueueFlags struct {
	repo       string
	issueType  string
	label      string
	initiative string
}

var readyQueueFlagNames = []string{"repo", "type", "label", "initiative"}

func (v *readyQueueFlags) register(cmd *cobra.Command) {
	f := cmd.Flags()
	f.StringVar(&v.repo, "repo", "", "Only issues on this repo (empty string for issues on no repo)")
	f.StringVar(&v.issueType, "type", "", "Only this type: "+strings.Join(api.IssueTypes, ", ")+" (decisions only when named)")
	f.StringVar(&v.label, "label", "", "Only issues carrying this label")
	f.StringVar(&v.initiative, "initiative", "", "Only issues in this initiative, by name or id")
}

func (v *readyQueueFlags) filter(cmd *cobra.Command) (api.ReadyFilter, error) {
	if err := validateIssueType(cmd.Flags(), "type", v.issueType); err != nil {
		return api.ReadyFilter{}, err
	}
	return api.ReadyFilter{
		Repo:       repoFlagValue(cmd, v.repo),
		Type:       v.issueType,
		Label:      v.label,
		Initiative: v.initiative,
	}, nil
}

// --- Reads of one issue ---

func newIssuesShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <issue>",
		Short:   "Show an issue with its edges, children and comments",
		Example: "  icb issues show 412\n  icb issues show 412 --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			issue, err := client.GetIssue(cmd.Context(), args[0], issueZone())
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), issue)
			}
			printIssueDetail(cmd.OutOrStdout(), issue, time.Now())
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the issue as JSON to stdout")
	return cmd
}

func newIssuesCommentsCommand() *cobra.Command {
	var (
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:     "comments <issue>",
		Short:   "List an issue's comments, oldest first",
		Long:    "Each row's #n is its place in the thread, which `remove-comment` takes.",
		Example: "  icb issues comments 412\n  icb issues comments 412 --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			comments, err := client.ListIssueComments(cmd.Context(), args[0], limitFlag(cmd))
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), comments)
			}
			if len(comments) == 0 {
				_, _ = fmt.Fprintln(cmd.OutOrStdout(), "No comments.")
				return nil
			}
			printIssueComments(cmd.OutOrStdout(), comments)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output comments as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newIssuesVocabularyCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "vocabulary",
		Short:   "List the values --status, --type, --priority and --label accept",
		Example: "  icb issues vocabulary\n  icb issues vocabulary --json",
		Args:    noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			vocabulary, err := client.GetIssueVocabulary(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), vocabulary)
			}
			printIssueVocabulary(cmd.OutOrStdout(), vocabulary)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the vocabulary as JSON to stdout")
	return cmd
}

// --- Identity ---

// actorIdentity names who acts when a claim or a comment does not say: the
// Claude Code session when run inside one, else user@host. Two sessions on one
// machine must not share a name, because a claimant extends its own claim.
func actorIdentity() string {
	if session := os.Getenv("CLAUDE_CODE_SESSION_ID"); session != "" {
		return "claude-code/" + session
	}
	user := os.Getenv("USER")
	if user == "" {
		user = "unknown"
	}
	host, err := os.Hostname()
	if err != nil || host == "" {
		return user
	}
	return user + "@" + host
}

// --- Rendering ---

func printIssuesTable(out io.Writer, issues []api.Issue, now time.Time) {
	if len(issues) == 0 {
		_, _ = fmt.Fprintln(out, "No issues.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "#\tPRIORITY\tTYPE\tSTATUS\tREPO\tTITLE")
	for _, issue := range issues {
		title := issue.Title
		if notes := issueStateNotes(issue, now); len(notes) > 0 {
			title += "  [" + strings.Join(notes, "; ") + "]"
		}
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\t%s\t%s\t%s\n",
			issue.Number, priorityCell(issue), issue.Type, issue.Status, orDash(strValue(issue.Repo)), title)
	}
	_ = tw.Flush()
}

// priorityCell shows the priority the queue sorts by, starred when inherited.
func priorityCell(issue api.Issue) string {
	name := priorityName(issue.EffectivePriority)
	if issue.EffectivePriority != issue.Priority {
		return name + "*"
	}
	return name
}

func orDash(s string) string {
	if s == "" {
		return "—"
	}
	return s
}

func isClosedIssue(issue api.Issue) bool {
	return issue.Status == api.IssueStatusCompleted || issue.Status == api.IssueStatusCanceled
}

// issueStateNotes says why an unclosed issue is or is not ready, in the words a
// reader acts on. A closed issue needs none: its status says it.
func issueStateNotes(issue api.Issue, now time.Time) []string {
	if isClosedIssue(issue) {
		return nil
	}
	var notes []string
	if claim := claimNote(issue, now); claim != "" {
		notes = append(notes, claim)
	}
	if blockers := openNumbers(issue.DependsOn); len(blockers) > 0 {
		notes = append(notes, "blocked by "+strings.Join(blockers, ", "))
	}
	if day := strValue(issue.DeferredUntilDate); day != "" && day > now.Local().Format(dayLayout) {
		notes = append(notes, "deferred until "+day)
	}
	if issue.OpenChildCount > 0 {
		notes = append(notes, fmt.Sprintf("%d open %s", issue.OpenChildCount, plural(issue.OpenChildCount, "child", "children")))
	}
	return notes
}

func claimNote(issue api.Issue, now time.Time) string {
	if issue.Status != api.IssueStatusInProgress {
		return ""
	}
	if issue.ClaimExpiresTS == nil || issue.ClaimedBy == nil {
		return "in progress with no claim"
	}
	if !issue.ClaimExpiresTS.After(now) {
		return "claim by " + *issue.ClaimedBy + " expired"
	}
	return "claimed by " + *issue.ClaimedBy + " until " + localClock(*issue.ClaimExpiresTS, now)
}

// localClock prints an instant as a time of day when it falls today here, and
// with its day otherwise.
func localClock(t, now time.Time) string {
	local := t.Local()
	if local.Format(dayLayout) == now.Local().Format(dayLayout) {
		return local.Format("15:04")
	}
	return local.Format("2006-01-02 15:04")
}

func openNumbers(summaries []api.IssueSummary) []string {
	var numbers []string
	for _, summary := range summaries {
		if summary.Status != api.IssueStatusCompleted && summary.Status != api.IssueStatusCanceled {
			numbers = append(numbers, "#"+strconv.Itoa(summary.Number))
		}
	}
	return numbers
}

func plural(n int, one, many string) string {
	if n == 1 {
		return one
	}
	return many
}

func summaryLine(summary api.IssueSummary) string {
	return fmt.Sprintf("%s %d %s", summaryMark(summary.Status), summary.Number, summary.Title)
}

func summaryMark(status string) string {
	switch status {
	case api.IssueStatusCompleted:
		return markCompleted
	case api.IssueStatusCanceled:
		return markArchived
	default:
		return markOpen
	}
}

func printIssueDetail(out io.Writer, issue api.IssueDetail, now time.Time) {
	_, _ = fmt.Fprintf(out, "#%d %s\n", issue.Number, issue.Title)
	field := func(label, value string) {
		if value != "" {
			_, _ = fmt.Fprintf(out, "  %-12s %s\n", label+":", value)
		}
	}
	field("type", issue.Type)
	status := issue.Status
	if notes := issueStateNotes(issue.Issue, now); len(notes) > 0 {
		status += " — " + strings.Join(notes, "; ")
	} else if issue.IsReady {
		status += " — ready"
	}
	field("status", status)
	field("reason", strValue(issue.StatusReason))
	if issue.DuplicateOf != nil {
		field("duplicate of", summaryLine(*issue.DuplicateOf))
	}
	priority := priorityName(issue.EffectivePriority)
	if issue.EffectivePriority != issue.Priority {
		priority += " (inherited; its own is " + priorityName(issue.Priority) + ")"
	}
	field("priority", priority)
	field("repo", orDash(strValue(issue.Repo)))
	if issue.Initiative != nil {
		field("initiative", issue.Initiative.Name)
	}
	if issue.Parent != nil {
		field("parent", summaryLine(*issue.Parent))
	}
	if issue.DiscoveredFrom != nil {
		field("found in", summaryLine(*issue.DiscoveredFrom))
	}
	field("labels", strings.Join(issue.Labels, ", "))
	field("deferred", strValue(issue.DeferredUntilDate))
	field("created", localDay(issue.CreatedTS))
	if issue.ClosedTS != nil {
		field("closed", localDay(*issue.ClosedTS))
	}

	section := func(title, body string) {
		if body != "" {
			_, _ = fmt.Fprintf(out, "\n%s:\n%s\n", title, indent(body, "  "))
		}
	}
	section("Description", strValue(issue.Description))
	section("Acceptance", strValue(issue.Acceptance))

	edges := func(title string, summaries []api.IssueSummary) {
		if len(summaries) == 0 {
			return
		}
		_, _ = fmt.Fprintf(out, "\n%s (%d):\n", title, len(summaries))
		for _, summary := range summaries {
			_, _ = fmt.Fprintf(out, "  %s\n", summaryLine(summary))
		}
	}
	edges("Depends on", issue.DependsOn)
	edges("Blocks", issue.Blocks)
	edges("Children", issue.Children)

	if len(issue.Comments) > 0 {
		_, _ = fmt.Fprintf(out, "\nComments (%d):\n", len(issue.Comments))
		printIssueComments(out, issue.Comments)
	}
}

func printIssueComments(out io.Writer, comments []api.IssueComment) {
	for i, comment := range comments {
		if i > 0 {
			_, _ = fmt.Fprintln(out)
		}
		_, _ = fmt.Fprintf(out, "  #%d  %s  %s\n", i+1, comment.CreatedTS.Local().Format("2006-01-02 15:04"), orDash(strValue(comment.Author)))
		_, _ = fmt.Fprintln(out, indent(comment.Body, "      "))
	}
}

func indent(text, prefix string) string {
	lines := strings.Split(strings.TrimRight(text, "\n"), "\n")
	for i, line := range lines {
		if line != "" {
			lines[i] = prefix + line
		}
	}
	return strings.Join(lines, "\n")
}

func printIssueVocabulary(out io.Writer, v api.IssueVocabulary) {
	_, _ = fmt.Fprintf(out, "statuses:     %s\n", strings.Join(v.Statuses, ", "))
	_, _ = fmt.Fprintf(out, "types:        %s\n", strings.Join(v.Types, ", "))
	priorities := make([]string, 0, len(v.Priorities))
	for _, p := range v.Priorities {
		priorities = append(priorities, fmt.Sprintf("%d %s", p.Value, p.Name))
	}
	_, _ = fmt.Fprintf(out, "priorities:   %s\n", strings.Join(priorities, ", "))
	_, _ = fmt.Fprintf(out, "initiatives:  %s\n", strings.Join(v.InitiativeStatuses, ", "))
	_, _ = fmt.Fprintln(out, "\nlabels:")
	printIssueLabels(out, v.Labels)
}
