package cli

import (
	"context"
	"errors"
	"fmt"
	"io"
	"sort"
	"strings"
	"sync"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
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
	Tasks           []api.Task
	CurrentHabits   []api.Habit
	CompletedHabits []api.HabitCompleted
	OwnedBooks      []api.Book
	CurrentArticle  *api.Article
	UnreadArticles  []api.Article
	Items           []api.ProjectItem
	BlockedItems    []api.ProjectItem
	Countdowns      []api.Countdown
	Events          []api.Event
	Failures        []sectionFailure
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
		Example: "  icb overview\n  icb overview --json\n  icb overview --limit 0",
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
			printOverview(cmd.OutOrStdout(), report)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the overview as JSON to stdout")
	cmd.Flags().IntVar(&limit, "limit", defaultOverviewLimit, "Max items per section (0 for no cap)")
	return cmd
}

// overviewFetches is the fan-out table. Habit completions are queried over a
// window that starts a day early and ends two days late, then narrowed to the
// local day in Go: the API parses bare dates to midnight UTC instants, so
// start=end=today would be a zero-width window that matches nothing.
func overviewFetches() []overviewFetch {
	return []overviewFetch{
		{sectionTasks, "tasks", func(ctx context.Context, c *api.Client, d *overviewData) error {
			tasks, err := c.ListTodoTasks(ctx, nil)
			d.Tasks = tasks
			return err
		}},
		{sectionHabits, "habits", func(ctx context.Context, c *api.Client, d *overviewData) error {
			current := true
			habits, err := c.ListHabits(ctx, &current, nil)
			d.CurrentHabits = habits
			return err
		}},
		{sectionHabits, "habit completions", func(ctx context.Context, c *api.Client, d *overviewData) error {
			start, end := localDayWindow(time.Now())
			completed, err := c.ListCompletedHabits(ctx, api.CompletedTasksQuery{StartDate: start, EndDate: end})
			d.CompletedHabits = completed
			return err
		}},
		{sectionBooks, "books", func(ctx context.Context, c *api.Client, d *overviewData) error {
			books, err := c.ListBooks(ctx, "owned")
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
			articles, err := c.ListArticles(ctx, nil, nil, &unread)
			d.UnreadArticles = articles
			return err
		}},
		{sectionProjectItems, "project items", func(ctx context.Context, c *api.Client, d *overviewData) error {
			items, err := c.ListItems(ctx)
			d.Items = items
			return err
		}},
		{sectionProjectItems, "blocked items", func(ctx context.Context, c *api.Client, d *overviewData) error {
			blocked, err := c.ListBlockedItems(ctx)
			d.BlockedItems = blocked
			return err
		}},
		{sectionCountdowns, "countdowns", func(ctx context.Context, c *api.Client, d *overviewData) error {
			countdowns, err := c.ListCountdowns(ctx)
			d.Countdowns = countdowns
			return err
		}},
		{sectionEvents, "events", func(ctx context.Context, c *api.Client, d *overviewData) error {
			events, err := c.ListEvents(ctx)
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
	dueHabits, doneHabits := splitHabitsByCompletion(data.CurrentHabits, data.CompletedHabits, now)
	nextItems := nextProjectItems(data.Items, data.BlockedItems)
	nextBooks := booksByProgress(data.OwnedBooks, "unread")
	queuedArticles := articlesBehindCurrent(data.UnreadArticles, data.CurrentArticle)
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
			DueToday:       dueHabits,
			CompletedToday: doneHabits,
			CurrentTotal:   len(data.CurrentHabits),
		},
		Books: bookSection{
			Reading:     booksByProgress(data.OwnedBooks, "reading"),
			NextUp:      capItems(nextBooks, limit),
			NextUpTotal: len(nextBooks),
		},
		Articles: articleSection{
			Current:     data.CurrentArticle,
			Unread:      capItems(queuedArticles, limit),
			UnreadTotal: len(queuedArticles),
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

// localDayWindow returns bare-date bounds spanning the local day with a day of
// slack on each side. The API parses these to midnight UTC instants, so the
// slack is what guarantees the local day is inside the window whatever the
// offset; callers narrow the result to the exact day themselves.
func localDayWindow(now time.Time) (string, string) {
	const dateLayout = "2006-01-02"
	return now.AddDate(0, 0, -1).Format(dateLayout), now.AddDate(0, 0, 2).Format(dateLayout)
}

// splitHabitsByCompletion separates the current habits into those still due
// today and today's completions.
//
// Completions carry no habit id, so they are matched on name and category. A
// habit renamed after being completed today therefore reads as due again until
// its next completion — an API shape limitation, not a bug to work around here.
func splitHabitsByCompletion(current []api.Habit, completed []api.HabitCompleted, now time.Time) ([]api.Habit, []api.HabitCompleted) {
	var doneToday []api.HabitCompleted
	done := make(map[string]bool)
	for _, completion := range completed {
		if !sameLocalDay(completion.CompleteDate, now) {
			continue
		}
		doneToday = append(doneToday, completion)
		done[habitKey(completion.Name, completion.CategoryID)] = true
	}

	var due []api.Habit
	for _, habit := range current {
		if !done[habitKey(habit.Name, habit.CategoryID)] {
			due = append(due, habit)
		}
	}
	return due, doneToday
}

func habitKey(name string, categoryID int) string {
	return fmt.Sprintf("%d\x00%s", categoryID, name)
}

func sameLocalDay(moment time.Time, now time.Time) bool {
	momentYear, momentMonth, momentDay := moment.In(now.Location()).Date()
	nowYear, nowMonth, nowDay := now.Date()
	return momentYear == nowYear && momentMonth == nowMonth && momentDay == nowDay
}

// nextProjectItems returns the actionable items — not completed, not archived,
// not blocked — oldest first. There is no cross-project priority in the API
// (project positions are unset and per-item positions would cost one call per
// project), so longest-outstanding is the ordering that at least means something.
func nextProjectItems(all []api.ProjectItem, blocked []api.ProjectItem) []api.ProjectItem {
	isBlocked := make(map[string]bool, len(blocked))
	for _, item := range blocked {
		isBlocked[item.ID] = true
	}

	var next []api.ProjectItem
	for _, item := range all {
		if item.Completed || item.Archived || isBlocked[item.ID] {
			continue
		}
		next = append(next, item)
	}
	sort.SliceStable(next, func(a, b int) bool { return next[a].CreatedAt.Before(next[b].CreatedAt) })
	return next
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
		if !event.Date.Before(startOfDay) {
			upcoming = append(upcoming, event)
		}
	}
	sort.SliceStable(upcoming, func(a, b int) bool { return upcoming[a].Date.Before(upcoming[b].Date) })
	return upcoming
}

// capItems truncates to limit; a limit of zero or less means no cap.
func capItems[T any](items []T, limit int) []T {
	if limit <= 0 || len(items) <= limit {
		return items
	}
	return items[:limit]
}

func printOverview(out io.Writer, r overviewReport) {
	printTaskSection(out, r.Tasks)
	printHabitSection(out, r.Habits)
	printBookSection(out, r.Books)
	printArticleSection(out, r.Articles)
	printProjectItemSection(out, r.ProjectItems)
	printUpcomingSection(out, r.Countdowns, r.Events, r.GeneratedAt)

	if len(r.Warnings) > 0 {
		fmt.Fprintln(out, "\nWarnings")
		for _, warning := range r.Warnings {
			fmt.Fprintf(out, "  %s: %s\n", warning.Section, warning.Message)
		}
	}
}

func printTaskSection(out io.Writer, section taskSection) {
	fmt.Fprintf(out, "Tasks (%d open)\n", section.Total)
	if len(section.Items) == 0 {
		fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for i, task := range section.Items {
		if i >= printListCap {
			break
		}
		fmt.Fprintf(tw, "  %d\t%s\t%s\n", task.Priority, truncateTitle(task.Name), task.Category)
	}
	_ = tw.Flush()
}

func printHabitSection(out io.Writer, section habitSection) {
	fmt.Fprintf(out, "\nHabits (%d of %d done today)\n", len(section.CompletedToday), section.CurrentTotal)
	if len(section.DueToday) == 0 {
		fmt.Fprintln(out, "  (all done)")
		return
	}
	names := make([]string, 0, len(section.DueToday))
	for _, habit := range section.DueToday {
		names = append(names, habit.Name)
	}
	fmt.Fprintf(out, "  due: %s\n", strings.Join(names, ", "))
}

func printBookSection(out io.Writer, section bookSection) {
	fmt.Fprintf(out, "\nBooks (%d reading, %d queued)\n", len(section.Reading), section.NextUpTotal)
	if len(section.Reading) == 0 && len(section.NextUp) == 0 {
		fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for _, book := range section.Reading {
		fmt.Fprintf(tw, "  reading:\t%s\t%s\n", truncateTitle(book.Title), book.Author)
	}
	for i, book := range section.NextUp {
		if i >= printListCap {
			break
		}
		fmt.Fprintf(tw, "  next:\t%s\t%s\n", truncateTitle(book.Title), book.Author)
	}
	_ = tw.Flush()
}

func printArticleSection(out io.Writer, section articleSection) {
	fmt.Fprintf(out, "\nArticles (%d unread)\n", section.UnreadTotal)
	if section.Current == nil && len(section.Unread) == 0 {
		fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	if section.Current != nil {
		fmt.Fprintf(tw, "  reading:\t%s\n", truncateTitle(section.Current.Title))
	}
	for i, article := range section.Unread {
		if i >= printListCap {
			break
		}
		fmt.Fprintf(tw, "  next:\t%s\n", truncateTitle(article.Title))
	}
	_ = tw.Flush()
}

func printProjectItemSection(out io.Writer, section projectItemSection) {
	fmt.Fprintf(out, "\nProject items (%d next, %d blocked)\n", section.NextTotal, section.BlockedTotal)
	if section.NextTotal == 0 && section.BlockedTotal == 0 {
		fmt.Fprintln(out, "  (none)")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for i, item := range section.Next {
		if i >= printListCap {
			break
		}
		fmt.Fprintf(tw, "  next:\t%s\t%s\n", truncateTitle(item.Title), projectNames(item))
	}
	for i, item := range section.Blocked {
		if i >= printListCap {
			break
		}
		fmt.Fprintf(tw, "  blocked:\t%s\t%s\n", truncateTitle(item.Title), projectNames(item))
	}
	_ = tw.Flush()
}

// printUpcomingSection interleaves countdowns and events chronologically. They
// stay separate in the JSON — a consumer may want one without the other — but
// what is coming up next is a single question, so the human view merges them.
func printUpcomingSection(out io.Writer, countdowns countdownSection, events eventSection, now time.Time) {
	fmt.Fprintln(out, "\nUpcoming")
	if countdowns.Total == 0 && events.Total == 0 {
		fmt.Fprintln(out, "  (none)")
		return
	}

	entries := make([]upcomingEntry, 0, len(countdowns.Items)+len(events.Items))
	for _, countdown := range countdowns.Items {
		entries = append(entries, upcomingEntry{countdown.DueDate, countdown.Name, "countdown"})
	}
	for _, event := range events.Items {
		date := event.Date.In(now.Location()).Format("2006-01-02")
		entries = append(entries, upcomingEntry{date, event.Name, "event"})
	}
	sort.SliceStable(entries, func(a, b int) bool { return entries[a].date < entries[b].date })

	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	for i, entry := range entries {
		if i >= printListCap {
			break
		}
		fmt.Fprintf(tw, "  %s\t%s\t%s\n", entry.date, truncateTitle(entry.name), entry.kind)
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
