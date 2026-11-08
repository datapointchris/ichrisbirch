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

	"github.com/datapointchris/life/cli/internal/api"
)

const (
	// overviewSchemaVersion is the contract between this command and its
	// consumers (a terminal dashboard, and the wall and mobile renderers behind it).
	// Bump it only for a breaking reshape: consumers read fields defensively, so
	// additions are free.
	//
	// v2 split the old `reading` section into `books` and `articles`. They are
	// separate apps, and one section spanning two of them meant neither of its
	// counts described the pile it sat above.
	//
	// v3 removed `priority` from task rows. A task row's position in its list
	// is its rank.
	//
	// v4 removed the `issues` section.
	//
	// v5 removed the `project_items` section. Projects live in the projects app.
	overviewSchemaVersion = 5

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
	sectionTasks      = "tasks"
	sectionHabits     = "habits"
	sectionBooks      = "books"
	sectionArticles   = "articles"
	sectionCountdowns = "countdowns"
	sectionEvents     = "events"
)

// overviewReport is the stable JSON schema for `overview --json`: the "what is
// outstanding right now" snapshot composed from the endpoints `overviewFetches`
// names.
type overviewReport struct {
	SchemaVersion int               `json:"schema_version"`
	GeneratedAt   time.Time         `json:"generated_at"`
	Tasks         taskSection       `json:"tasks"`
	Habits        habitSection      `json:"habits"`
	Books         bookSection       `json:"books"`
	Articles      articleSection    `json:"articles"`
	Countdowns    countdownSection  `json:"countdowns"`
	Events        eventSection      `json:"events"`
	Warnings      []overviewWarning `json:"warnings"`
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
// is the one being read, Unread is the queue behind it, oldest saved first.
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
			"articles you are reading and what is next in each, and approaching countdowns\n" +
			"and events. Composed from those endpoints in one command so a dashboard needs\n" +
			"a single call.",
		Example: "  life overview\n  life overview --json\n  life overview --limit 3",
		Args:    cobra.NoArgs,
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
// derive their rows — the next books, the queued articles — so a server-side
// cap would cap the set before the derivation and take the wrong rows.
func overviewFetches() []overviewFetch {
	return []overviewFetch{
		{sectionTasks, "tasks", func(ctx context.Context, c *api.Client, d *overviewData) error {
			tasks, err := c.ListTasks(ctx, nil, api.TaskStatusOpen, "", api.Window{})
			d.Tasks = tasks
			return err
		}},
		{sectionHabits, "habits", func(ctx context.Context, c *api.Client, d *overviewData) error {
			board, err := c.GetHabitsDay(ctx, "", LocalZoneName())
			d.HabitsDay = board
			return err
		}},
		{sectionBooks, "books", func(ctx context.Context, c *api.Client, d *overviewData) error {
			books, err := c.ListBooks(ctx, api.BookFilter{Ownership: "owned"}, api.Window{}, "", nil)
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
			articles, err := c.ListArticles(ctx, nil, nil, &unread, api.Window{}, nil)
			d.UnreadArticles = articles
			return err
		}},
		// Archived is the read set. Marking an article read archives it in the same
		// call, so there is no separate read filter to ask for and no third state.
		{sectionArticles, "read articles", func(ctx context.Context, c *api.Client, d *overviewData) error {
			archived := true
			articles, err := c.ListArticles(ctx, nil, &archived, nil, api.Window{}, nil)
			d.ReadArticles = articles
			return err
		}},
		{sectionCountdowns, "countdowns", func(ctx context.Context, c *api.Client, d *overviewData) error {
			countdowns, err := c.ListCountdowns(ctx, nil)
			d.Countdowns = countdowns
			return err
		}},
		{sectionEvents, "events", func(ctx context.Context, c *api.Client, d *overviewData) error {
			events, err := c.ListEvents(ctx, api.EventsUpcoming, api.DayZone(LocalZoneName()), nil)
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
// untrustworthy rather than merely partial: a rejected session, a caller the
// API forbids a section, or every fetch failing. Without it, each such section
// prints as if it held nothing and the command exits 0, with the cause only in
// a warning on stderr. A service client is refused every section outside its
// scope.
func systemicOverviewFailure(failures []sectionFailure, total int) error {
	for _, failure := range failures {
		var apiErr *api.APIError
		if errors.As(failure.Err, &apiErr) && (apiErr.Unauthorized() || apiErr.Forbidden()) {
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
	nextBooks := booksByProgress(data.OwnedBooks, "unread")
	queuedArticles := articlesBehindCurrent(data.UnreadArticles, data.CurrentArticle)
	lastArticleRead, articlesReadInWindow := articleReadActivity(data.ReadArticles, now)
	countdowns := upcomingCountdowns(data.Countdowns, now)

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
		Countdowns: countdownSection{
			Items: capItems(countdowns, limit),
			Total: len(countdowns),
		},
		Events: eventSection{
			Items: capItems(data.Events, limit),
			Total: len(data.Events),
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

// articlesBehindCurrent is the unread queue, oldest saved first, with the one
// being read removed so it is never also counted as waiting. Oldest first keeps
// an old article at the head until it is read or deleted, so the backlog cannot
// silently keep what was saved years ago.
func articlesBehindCurrent(unread []api.Article, current *api.Article) []api.Article {
	var queued []api.Article
	for _, article := range unread {
		if current != nil && article.ID == current.ID {
			continue
		}
		queued = append(queued, article)
	}
	sort.SliceStable(queued, func(i, j int) bool { return queued[i].SaveDate.Before(queued[j].SaveDate) })
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

// capItems truncates to limit and always answers an allocated slice.
//
// Every section reaches the JSON through here, and a nil slice marshals to
// `null`. A section whose fetch failed has nothing to cap, so
// `jq '.habits.due_today[]'` would meet a null and exit 5 while life exited 0.
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
		_, _ = fmt.Fprintf(tw, "  %d\t%s\t%s\n", i+1, truncateTitle(task.Name), task.Category)
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
