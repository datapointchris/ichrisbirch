package cli

import (
	"context"
	"errors"
	"fmt"
	"io"
	"math"
	"sort"
	"strings"
	"sync"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

const (
	// overviewSchemaVersion is the contract between this command and its
	// consumers (menu dashboard, and the wall and mobile renderers behind it).
	// Bump it only for a breaking reshape: consumers read fields defensively, so
	// additions are free.
	//
	// v2 split the old `reading` section into `books` and `articles`. They are
	// separate apps, and one section spanning two of them meant neither of its
	// counts described the pile it sat above.
	overviewSchemaVersion = 2

	// defaultOverviewLimit caps each section so the payload stays a glance. Every
	// section reports its pre-cap total, so a capped list never lies about size.
	defaultOverviewLimit = 10

	// printListCap bounds the human view only, independently of the JSON caps.
	printListCap = 5

	// overviewTimeout bounds the whole fan-out: the injected oauth2 client sets no
	// timeout of its own, so without this a hung handshake hangs the command.
	overviewTimeout = 15 * time.Second

	// articleReadWindow is how far back read_last_30_days counts. The window is in
	// the field name rather than beside it, so a consumer cannot label a count it
	// has mislabeled: change the window and the field a renderer reads disappears
	// rather than quietly meaning something else.
	articleReadWindow = 30 * 24 * time.Hour
)

// Section names, shared by the fetch table and the warnings so a consumer can
// tell which part of the snapshot degraded.
const (
	sectionTasks        = "tasks"
	sectionHabits       = "habits"
	sectionBooks        = "books"
	sectionArticles     = "articles"
	sectionProjectItems = "project_items"
	sectionCountdowns   = "countdowns"
	sectionEvents       = "events"
)

// overviewReport is the stable JSON schema for `overview --json`: the "what is
// outstanding right now" snapshot composed from the task, habit, book, article,
// project-item, countdown, and event endpoints.
type overviewReport struct {
	SchemaVersion int                `json:"schema_version"`
	GeneratedAt   time.Time          `json:"generated_at"`
	Tasks         taskSection        `json:"tasks"`
	Habits        habitSection       `json:"habits"`
	Books         bookSection        `json:"books"`
	Articles      articleSection     `json:"articles"`
	ProjectItems  projectItemSection `json:"project_items"`
	Countdowns    countdownSection   `json:"countdowns"`
	Events        eventSection       `json:"events"`
	Warnings      []overviewWarning  `json:"warnings"`
}

type taskSection struct {
	Items []api.Task `json:"items"`
	Total int        `json:"total"`
}

type habitSection struct {
	DueToday       []api.Habit          `json:"due_today"`
	CompletedToday []api.HabitCompleted `json:"completed_today"`
	CurrentTotal   int                  `json:"current_total"`
}

type bookSection struct {
	Reading     []api.Book `json:"reading"`
	NextUp      []api.Book `json:"next_up"`
	NextUpTotal int        `json:"next_up_total"`
}

// articleSection is the reading list, its own app with its own rhythm: Current
// is the one being read, Unread is the queue behind it.
type articleSection struct {
	Current     *api.Article  `json:"current"`
	Unread      []api.Article `json:"unread"`
	UnreadTotal int           `json:"unread_total"`

	// An unread count only ever climbs, so on its own it cannot answer whether any
	// of the pile is being read. These two say when one last was and how many were
	// inside the window, which is the question a saved-article backlog is kept to
	// answer. Null when nothing has ever been read.
	LastReadAt     *time.Time `json:"last_read_at"`
	ReadLast30Days int        `json:"read_last_30_days"`
}

type projectItemSection struct {
	Next         []api.ProjectItem `json:"next"`
	NextTotal    int               `json:"next_total"`
	Blocked      []api.ProjectItem `json:"blocked"`
	BlockedTotal int               `json:"blocked_total"`
}

type countdownSection struct {
	Items []api.Countdown `json:"items"`
	Total int             `json:"total"`
}

type eventSection struct {
	Items []api.Event `json:"items"`
	Total int         `json:"total"`
}

// overviewWarning reports one degraded fetch. It is keyed by section so a
// consumer can mark the affected lane unavailable without guessing from prose.
type overviewWarning struct {
	Section string `json:"section"`
	Message string `json:"message"`
}

// overviewData is the raw fan-out result: every endpoint's payload plus the
// failures that kept some of them empty.
type overviewData struct {
	Tasks          []api.Task
	HabitsDay      api.HabitsDay
	OwnedBooks     []api.Book
	CurrentArticle *api.Article
	UnreadArticles []api.Article
	ReadArticles   []api.Article
	Items          []api.ProjectItem
	BlockedItems   []api.ProjectItem
	Countdowns     []api.Countdown
	Events         []api.Event
	Failures       []sectionFailure
}

type sectionFailure struct {
	Section string
	Label   string
	Err     error
}

// overviewFetch is one endpoint call. Each writes a distinct field of the shared
// overviewData, so the goroutines never touch the same memory.
type overviewFetch struct {
	section string
	label   string
	run     func(ctx context.Context, client *api.Client, data *overviewData) error
}

func newOverviewCommand() *cobra.Command {
	var (
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "overview",
		Short: "Show everything outstanding right now across the apps",
		Long: "A cross-cutting snapshot: open tasks, habits still due today, the books and\n" +
			"articles you are reading and what is next in each, the next and blocked\n" +
			"project items with the projects they belong to, and approaching countdowns\n" +
			"and events. Composed from those endpoints in one command so a dashboard\n" +
			"needs a single call.",
		Example: "  icb overview\n  icb overview --json\n  icb overview --limit 3",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			ctx, cancel := context.WithTimeout(cmd.Context(), overviewTimeout)
			defer cancel()

			data := fetchOverview(ctx, client)
			if err := systemicOverviewFailure(data.Failures, len(overviewFetches())); err != nil {
				return handleAPIError(err)
			}

			report := buildOverview(data, time.Now(), limit)
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), report)
			}
			printOverview(cmd.OutOrStdout(), cmd.ErrOrStderr(), report)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the overview as JSON to stdout")
	addCapFlag(cmd, &limit, defaultOverviewLimit, "Maximum number of items to show per section")
	return cmd
}

// overviewFetches is the fan-out table. Every fetch passes a nil limit, and
// --limit is applied by capItems after the sections are built. Several of them
// derive their rows — the next books, the queued articles, the unblocked
// items — so a server-side cap would cap the set before the derivation and
// take the wrong rows.
func overviewFetches() []overviewFetch {
	return []overviewFetch{
		{sectionTasks, "tasks", func(ctx context.Context, c *api.Client, d *overviewData) error {
			tasks, err := c.ListTasks(ctx, nil, api.TaskStatusOpen, "", "", "", "")
			d.Tasks = tasks
			return err
		}},
		{sectionHabits, "habits", func(ctx context.Context, c *api.Client, d *overviewData) error {
			board, err := c.GetHabitsDay(ctx, "", LocalZoneName())
			d.HabitsDay = board
			return err
		}},
		{sectionBooks, "books", func(ctx context.Context, c *api.Client, d *overviewData) error {
			books, err := c.ListBooks(ctx, api.BookFilter{Ownership: "owned"}, "", "", nil)
			d.OwnedBooks = books
			return err
		}},
		{sectionArticles, "current article", func(ctx context.Context, c *api.Client, d *overviewData) error {
			article, err := c.GetCurrentArticle(ctx)
			d.CurrentArticle = article
			return err
		}},
		{sectionArticles, "unread articles", func(ctx context.Context, c *api.Client, d *overviewData) error {
			unread := true
			articles, err := c.ListArticles(ctx, nil, nil, &unread, "", "", "", nil)
			d.UnreadArticles = articles
			return err
		}},
		// Archived is the read set. Marking an article read archives it in the same
		// call, so there is no separate read filter to ask for and no third state.
		{sectionArticles, "read articles", func(ctx context.Context, c *api.Client, d *overviewData) error {
			archived := true
			articles, err := c.ListArticles(ctx, nil, &archived, nil, "", "", "", nil)
			d.ReadArticles = articles
			return err
		}},
		{sectionProjectItems, "project items", func(ctx context.Context, c *api.Client, d *overviewData) error {
			items, err := c.ListItems(ctx, nil, api.ItemStatusOpen, "", "", "", nil)
			d.Items = items
			return err
		}},
		{sectionProjectItems, "blocked items", func(ctx context.Context, c *api.Client, d *overviewData) error {
			blocked, err := c.ListBlockedItems(ctx, nil)
			d.BlockedItems = blocked
			return err
		}},
		{sectionCountdowns, "countdowns", func(ctx context.Context, c *api.Client, d *overviewData) error {
			countdowns, err := c.ListCountdowns(ctx, nil)
			d.Countdowns = countdowns
			return err
		}},
		{sectionEvents, "events", func(ctx context.Context, c *api.Client, d *overviewData) error {
			events, err := c.ListEvents(ctx, nil)
			d.Events = events
			return err
		}},
	}
}

// fetchOverview runs every endpoint concurrently. A failure is recorded against
// its section and leaves that field zero — one dead endpoint must not cost the
// rest of the snapshot, which is why this is a WaitGroup and not an errgroup.
func fetchOverview(ctx context.Context, client *api.Client) overviewData {
	fetches := overviewFetches()
	var data overviewData
	errs := make([]error, len(fetches))

	var wg sync.WaitGroup
	for i, fetch := range fetches {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs[i] = fetch.run(ctx, client, &data)
		}()
	}
	wg.Wait()

	for i, err := range errs {
		if err != nil {
			data.Failures = append(data.Failures, sectionFailure{fetches[i].section, fetches[i].label, err})
		}
	}
	return data
}

// systemicOverviewFailure reports the failures that make the whole snapshot
// untrustworthy rather than merely partial: a rejected session, or every fetch
// failing. Returning a partial payload in those cases would be a lie.
func systemicOverviewFailure(failures []sectionFailure, total int) error {
	for _, failure := range failures {
		var apiErr *api.APIError
		if errors.As(failure.Err, &apiErr) && apiErr.Unauthorized() {
			return failure.Err
		}
	}
	if total > 0 && len(failures) == total {
		return failures[0].Err
	}
	return nil
}

// buildOverview composes the report. It is pure — no clock, no network — so the
// filtering, ordering, and capping rules are directly testable.
func buildOverview(data overviewData, now time.Time, limit int) overviewReport {
	nextItems := overviewProjectItems(data.Items, data.BlockedItems)
	nextBooks := booksByProgress(data.OwnedBooks, "unread")
	queuedArticles := articlesBehindCurrent(data.UnreadArticles, data.CurrentArticle)
	lastArticleRead, articlesReadInWindow := articleReadActivity(data.ReadArticles, now)
	countdowns := upcomingCountdowns(data.Countdowns, now)
	events := upcomingEvents(data.Events, now)

	report := overviewReport{
		SchemaVersion: overviewSchemaVersion,
		GeneratedAt:   now,
		Tasks: taskSection{
			Items: capItems(data.Tasks, limit),
			Total: len(data.Tasks),
		},
		Habits: habitSection{
			DueToday:       capItems(data.HabitsDay.Due, limit),
			CompletedToday: capItems(data.HabitsDay.Completed, limit),
			CurrentTotal:   data.HabitsDay.CurrentTotal,
		},
		Books: bookSection{
			Reading:     capItems(booksByProgress(data.OwnedBooks, "reading"), limit),
			NextUp:      capItems(nextBooks, limit),
			NextUpTotal: len(nextBooks),
		},
		Articles: articleSection{
			Current:        data.CurrentArticle,
			Unread:         capItems(queuedArticles, limit),
			UnreadTotal:    len(queuedArticles),
			LastReadAt:     lastArticleRead,
			ReadLast30Days: articlesReadInWindow,
		},
		ProjectItems: projectItemSection{
			Next:         capItems(nextItems, limit),
			NextTotal:    len(nextItems),
			Blocked:      capItems(data.BlockedItems, limit),
			BlockedTotal: len(data.BlockedItems),
		},
		Countdowns: countdownSection{
			Items: capItems(countdowns, limit),
			Total: len(countdowns),
		},
		Events: eventSection{
			Items: capItems(events, limit),
			Total: len(events),
		},
	}
	// Always an array, never null: consumers branch on this to mark a lane
	// degraded, so it must not be ambiguous when everything succeeded.
	report.Warnings = make([]overviewWarning, 0, len(data.Failures))
	for _, failure := range data.Failures {
		report.Warnings = append(report.Warnings, overviewWarning{
			Section: failure.Section,
			Message: fmt.Sprintf("%s: %s", failure.Label, failure.Err),
		})
	}
	return report
}

// actionableItems returns the items that can be taken now — not completed, not
// archived, not blocked — in the order they are taken: the whole queue of the
// highest-ranked project, then the next project's, each queue in its own
// position order. This is the order `projects items next` prints.
//
// A kind narrows the queue as well as the items. Only projects of that kind
// rank, so an item that is also in a higher-ranked project of another kind is
// queued where it sits in its own kind's project. An empty kind is every project.
func actionableItems(all []api.ProjectItem, blocked []api.ProjectItem, kind string) []api.ProjectItem {
	isBlocked := make(map[string]bool, len(blocked))
	for _, item := range blocked {
		isBlocked[item.ID] = true
	}

	var next []api.ProjectItem
	for _, item := range itemsOfKind(all, kind) {
		if item.Completed || item.Archived || isBlocked[item.ID] {
			continue
		}
		next = append(next, item)
	}
	sort.SliceStable(next, func(a, b int) bool { return takenBefore(next[a], next[b], kind) })
	return next
}

// overviewProjectItems is the overview's view of the same queue, interleaved a
// project at a time so no single project can fill the overview cap.
//
// Taking the queue in order lets the highest-ranked project hold every one of
// the ten rows, leaving the next project with nothing on the board. Position
// picks which item represents a project; it does not decide how many slots that
// project gets.
func overviewProjectItems(all []api.ProjectItem, blocked []api.ProjectItem) []api.ProjectItem {
	return interleaveByProject(actionableItems(all, blocked, ""))
}

// takenBefore orders two items by the rank of the project each is drawn under,
// then by where each is queued in that project. Creation time and id settle
// what remains, which is also the whole order when the API sends no positions.
func takenBefore(a api.ProjectItem, b api.ProjectItem, kind string) bool {
	projectA, projectB := primaryProject(a, kind), primaryProject(b, kind)
	if projectA.ID != projectB.ID {
		return outranks(projectA, projectB)
	}
	if queuedA, queuedB := queuePosition(a, projectA.ID), queuePosition(b, projectB.ID); queuedA != queuedB {
		return queuedA < queuedB
	}
	if !a.CreatedAt.Equal(b.CreatedAt) {
		return a.CreatedAt.Before(b.CreatedAt)
	}
	return a.ID < b.ID
}

// queuePosition is where an item is queued in one project. An item with no
// membership there sorts after every item that has one.
func queuePosition(item api.ProjectItem, projectID string) int {
	for _, membership := range item.Memberships {
		if membership.ProjectID == projectID {
			return membership.Position
		}
	}
	return math.MaxInt
}

// interleaveByProject takes one item from each project in turn, so a project
// with twenty queued items and one with a single item are equally represented in
// the first round. Items arrive in the order they should be drawn within their
// own project and keep it.
func interleaveByProject(items []api.ProjectItem) []api.ProjectItem {
	queues := make(map[string][]api.ProjectItem)
	var order []api.Project
	longest := 0

	for _, item := range items {
		project := primaryProject(item, "")
		if _, seen := queues[project.ID]; !seen {
			order = append(order, project)
		}
		queues[project.ID] = append(queues[project.ID], item)
		if queued := len(queues[project.ID]); queued > longest {
			longest = queued
		}
	}
	sort.SliceStable(order, func(a, b int) bool { return outranks(order[a], order[b]) })

	interleaved := make([]api.ProjectItem, 0, len(items))
	for round := range longest {
		for _, project := range order {
			if queue := queues[project.ID]; round < len(queue) {
				interleaved = append(interleaved, queue[round])
			}
		}
	}
	return interleaved
}

// primaryProject is the project an item is drawn under. An item can belong to
// several, so it competes in the round of the highest-priority one rather than
// once per membership — otherwise multi-project items get a slot per project.
// Items belonging to no project share the zero value, which keeps them in one
// queue instead of making each its own round. A kind limits the candidates to
// projects of that kind; an empty kind considers every project.
func primaryProject(item api.ProjectItem, kind string) api.Project {
	var primary api.Project
	found := false
	for _, project := range item.Projects {
		if kind != "" && project.Kind != kind {
			continue
		}
		if !found || outranks(project, primary) {
			primary = project
			found = true
		}
	}
	return primary
}

// outranks orders projects by the position the API already exposes. Positions
// are largely unset, so creation time then id break the tie — arbitrary, but
// stable, which is what keeps the board from reshuffling between refreshes.
func outranks(a api.Project, b api.Project) bool {
	if a.Position != b.Position {
		return a.Position < b.Position
	}
	if !a.CreatedAt.Equal(b.CreatedAt) {
		return a.CreatedAt.Before(b.CreatedAt)
	}
	return a.ID < b.ID
}

// articleReadActivity is when an article was last read and how many were read
// inside articleReadWindow.
//
// An archived article with no LastReadDate is skipped rather than counted, so a
// row archived by some other route cannot report itself as reading that happened.
func articleReadActivity(read []api.Article, now time.Time) (*time.Time, int) {
	var last *time.Time
	inWindow := 0
	cutoff := now.Add(-articleReadWindow)
	for i := range read {
		when := read[i].LastReadDate
		if when == nil {
			continue
		}
		if last == nil || when.After(*last) {
			last = when
		}
		if when.After(cutoff) {
			inWindow++
		}
	}
	return last, inWindow
}

// articlesBehindCurrent is the unread queue with the one being read removed, so
// the current article is never also counted as waiting.
func articlesBehindCurrent(unread []api.Article, current *api.Article) []api.Article {
	var queued []api.Article
	for _, article := range unread {
		if current != nil && article.ID == current.ID {
			continue
		}
		queued = append(queued, article)
	}
	return queued
}

// booksByProgress filters an already ownership-filtered list, preserving the
// server's priority order.
func booksByProgress(books []api.Book, progress string) []api.Book {
	var matched []api.Book
	for _, book := range books {
		if book.Progress == progress {
			matched = append(matched, book)
		}
	}
	return matched
}

func upcomingCountdowns(countdowns []api.Countdown, now time.Time) []api.Countdown {
	today := now.Format("2006-01-02")
	var upcoming []api.Countdown
	for _, countdown := range countdowns {
		if countdown.DueDate >= today {
			upcoming = append(upcoming, countdown)
		}
	}
	sort.SliceStable(upcoming, func(a, b int) bool { return upcoming[a].DueDate < upcoming[b].DueDate })
	return upcoming
}

func upcomingEvents(events []api.Event, now time.Time) []api.Event {
	year, month, day := now.Date()
	startOfDay := time.Date(year, month, day, 0, 0, 0, 0, now.Location())

	var upcoming []api.Event
	for _, event := range events {
		if !api.EventInstant(event).Before(startOfDay) {
			upcoming = append(upcoming, event)
		}
	}
	sort.SliceStable(upcoming, func(a, b int) bool { return api.EventInstant(upcoming[a]).Before(api.EventInstant(upcoming[b])) })
	return upcoming
}

// capItems truncates to limit and always answers an allocated slice.
//
// Every section reaches the JSON through here, and a nil slice marshals to
// `null`. A section whose fetch failed has nothing to cap, so
// `jq '.habits.due_today[]'` would meet a null and exit 5 while icb exited 0.
//
// Zero is a row count like any other and caps to nothing, so it needs no branch
// of its own: len(items) <= 0 is false whenever there is anything to cut.
//
// A negative caps to nothing rather than panicking. The callers take their limit
// from a flag whose parser refuses one, but that guard lives on a type this
// signature never mentions, and a computed bound would reach items[:-1].
func capItems[T any](items []T, limit int) []T {
	if limit < 0 || len(items) == 0 {
		return []T{}
	}
	if len(items) <= limit {
		return items
	}
	return items[:limit]
}

// printOverview renders the report for a human. Warnings go to errOut, not out:
// a degraded section is a diagnostic about the fetch, and mixing it into the
// snapshot corrupts the stream for anything reading the plain output. In --json
// mode they stay in the payload, where they are part of the schema.
func printOverview(out, errOut io.Writer, r overviewReport) {
	printTaskSection(out, r.Tasks)
	printHabitSection(out, r.Habits)
	printBookSection(out, r.Books)
	printArticleSection(out, r.Articles)
	printProjectItemSection(out, r.ProjectItems)
	printUpcomingSection(out, r.Countdowns, r.Events, r.GeneratedAt)

	for _, warning := range r.Warnings {
		_, _ = fmt.Fprintf(errOut, "warning: %s: %s\n", warning.Section, warning.Message)
	}
}

func printTaskSection(out io.Writer, section taskSection) {
	_, _ = fmt.Fprintf(out, "Tasks (%d open)\n", section.Total)
	if len(section.Items) == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for i, task := range section.Items {
		if i >= printListCap {
			break
		}
		_, _ = fmt.Fprintf(tw, "  %d\t%s\t%s\n", task.Priority, truncateTitle(task.Name), task.Category)
	}
	_ = tw.Flush()
}

func printHabitSection(out io.Writer, section habitSection) {
	_, _ = fmt.Fprintf(out, "\nHabits (%d of %d done today)\n", len(section.CompletedToday), section.CurrentTotal)
	if len(section.DueToday) == 0 {
		_, _ = fmt.Fprintln(out, "  (all done)")
		return
	}
	names := make([]string, 0, len(section.DueToday))
	for _, habit := range section.DueToday {
		names = append(names, habit.Name)
	}
	_, _ = fmt.Fprintf(out, "  due: %s\n", strings.Join(names, ", "))
}

func printBookSection(out io.Writer, section bookSection) {
	_, _ = fmt.Fprintf(out, "\nBooks (%d reading, %d queued)\n", len(section.Reading), section.NextUpTotal)
	if len(section.Reading) == 0 && len(section.NextUp) == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for _, book := range section.Reading {
		_, _ = fmt.Fprintf(tw, "  reading:\t%s\t%s\n", truncateTitle(book.Title), book.Author)
	}
	for i, book := range section.NextUp {
		if i >= printListCap {
			break
		}
		_, _ = fmt.Fprintf(tw, "  next:\t%s\t%s\n", truncateTitle(book.Title), book.Author)
	}
	_ = tw.Flush()
}

// articleReadSummary is the clause that says whether the pile is moving. Empty
// when nothing has ever been read: "0 read" beside a list nobody has touched adds
// no fact the unread count did not already carry.
func articleReadSummary(section articleSection) string {
	if section.LastReadAt == nil {
		return ""
	}
	return fmt.Sprintf(", %d read in 30d, last %s",
		section.ReadLast30Days, localDay(*section.LastReadAt))
}

func printArticleSection(out io.Writer, section articleSection) {
	_, _ = fmt.Fprintf(out, "\nArticles (%d unread%s)\n", section.UnreadTotal, articleReadSummary(section))
	if section.Current == nil && len(section.Unread) == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	if section.Current != nil {
		_, _ = fmt.Fprintf(tw, "  reading:\t%s\n", truncateTitle(section.Current.Title))
	}
	for i, article := range section.Unread {
		if i >= printListCap {
			break
		}
		_, _ = fmt.Fprintf(tw, "  next:\t%s\n", truncateTitle(article.Title))
	}
	_ = tw.Flush()
}

func printProjectItemSection(out io.Writer, section projectItemSection) {
	_, _ = fmt.Fprintf(out, "\nProject items (%d next, %d blocked)\n", section.NextTotal, section.BlockedTotal)
	if section.NextTotal == 0 && section.BlockedTotal == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for i, item := range section.Next {
		if i >= printListCap {
			break
		}
		_, _ = fmt.Fprintf(tw, "  next:\t%s\t%s\n", truncateTitle(item.Title), projectNames(item))
	}
	for i, item := range section.Blocked {
		if i >= printListCap {
			break
		}
		_, _ = fmt.Fprintf(tw, "  blocked:\t%s\t%s\n", truncateTitle(item.Title), projectNames(item))
	}
	_ = tw.Flush()
}

// printUpcomingSection interleaves countdowns and events chronologically. They
// stay separate in the JSON — a consumer may want one without the other — but
// what is coming up next is a single question, so the human view merges them.
func printUpcomingSection(out io.Writer, countdowns countdownSection, events eventSection, now time.Time) {
	_, _ = fmt.Fprintln(out, "\nUpcoming")
	if countdowns.Total == 0 && events.Total == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
		return
	}

	entries := make([]upcomingEntry, 0, len(countdowns.Items)+len(events.Items))
	for _, countdown := range countdowns.Items {
		entries = append(entries, upcomingEntry{countdown.DueDate, countdown.Name, "countdown"})
	}
	for _, event := range events.Items {
		date := api.EventInstant(event).In(now.Location()).Format("2006-01-02")
		entries = append(entries, upcomingEntry{date, event.Name, "event"})
	}
	sort.SliceStable(entries, func(a, b int) bool { return entries[a].date < entries[b].date })

	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for i, entry := range entries {
		if i >= printListCap {
			break
		}
		_, _ = fmt.Fprintf(tw, "  %s\t%s\t%s\n", entry.date, truncateTitle(entry.name), entry.kind)
	}
	_ = tw.Flush()
}

// projectNames labels an item with the work it belongs to. An item can sit in
// several projects, so all of them are named rather than an arbitrary first.
func projectNames(item api.ProjectItem) string {
	names := make([]string, 0, len(item.Projects))
	for _, project := range item.Projects {
		names = append(names, project.Name)
	}
	return strings.Join(names, ", ")
}

type upcomingEntry struct {
	date string
	name string
	kind string
}

// truncateTitle fits a title into the column, collapsing it onto one line first:
// scraped article titles carry the source page's newlines and tabs, which would
// otherwise break the tabwriter's alignment and defeat the width limit.
func truncateTitle(title string) string {
	const titleWidth = 60
	title = strings.Join(strings.Fields(title), " ")
	runes := []rune(title)
	if len(runes) <= titleWidth {
		return title
	}
	return string(runes[:titleWidth-1]) + "…"
}
