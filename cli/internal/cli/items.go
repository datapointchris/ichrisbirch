package cli

import (
	"context"
	"errors"
	"fmt"
	"io"
	"slices"
	"sort"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/prompt"
	"github.com/datapointchris/ichrisbirch/cli/internal/repos"
)

func newItemsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "items",
		Short: "Work with project items — the structured to-do units in projects",
		Long: "The ordered work units inside a project, each with sub-tasks, dependencies,\n" +
			"and membership in one or more projects. Unstructured chores go in\n" +
			"`icb tasks` instead.",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newItemsListCommand(),
		newItemsNextCommand(),
		newItemsBlockedCommand(),
		newItemsSearchCommand(),
		newItemsShowCommand(),
		newItemsCreateCommand(),
		newItemsEditCommand(),
		newItemsCompletionCommand("complete", "Mark an item completed", true),
		newItemsCompletionCommand("reopen", "Reopen a completed item", false),
		newItemsArchiveCommand("archive", "Archive an item", true),
		newItemsArchiveCommand("unarchive", "Restore an archived item", false),
		newItemsDeleteCommand(),
		newItemsReorderCommand(),
		newItemsAddProjectCommand(),
		newItemsRemoveProjectCommand(),
		newItemsAddDependencyCommand(),
		newItemsRemoveDependencyCommand(),
		newItemsBlockersCommand(),
		newItemsTreeCommand(),
		newItemsTasksCommand(),
		newItemsAddTaskCommand(),
		newItemsCompleteTaskCommand(),
		newItemsEditTaskCommand(),
		newItemsRemoveTaskCommand(),
	)
	return cmd
}

// --- Reads over collections ---

func newItemsListCommand() *cobra.Command {
	var (
		asJSON     bool
		project    string
		repo       string
		itemStatus string
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List open items, or one project's items in order",
		Long: "Open means not completed and not archived, and it is the default because\n" +
			"completed items accumulate without bound — at the time this was added they\n" +
			"had reached parity with open ones, so the whole list read half history.\n" +
			"\n" +
			"--status takes one of: " + strings.Join(api.ItemStatuses, ", ") + ". They partition every\n" +
			"item, because archived beats completed: an item completed and then archived\n" +
			"answers to archived alone.\n" +
			"\n" +
			"--project selects which rows come back, not which states, so it narrows to\n" +
			"open the same way the unscoped list does and takes the same --status.",
		Example: "  icb projects items list\n" +
			"  icb projects items list --status completed\n" +
			"  icb projects items list --status all --json\n" +
			"  icb projects items list --repo dotfiles\n" +
			"  icb projects items list --project todoui\n" +
			"  icb projects items list --project todoui --status all",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if err := validateItemStatus(cmd, itemStatus); err != nil {
				return err
			}
			if project == "" {
				filter := repoFlagValue(cmd, repo)
				if err := runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
					return c.ListItems(cmd.Context(), filter, itemStatus)
				}); err != nil {
					return err
				}
				hintHiddenItems(cmd, asJSON, itemStatus)
				return nil
			}
			if cmd.Flags().Changed("repo") {
				return usageError{fmt.Errorf("--repo and --project are different questions — pass one")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			items, err := client.ListProjectItems(cmd.Context(), project, itemStatus)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), items)
			}
			printProjectItemsTable(cmd.OutOrStdout(), items)
			hintHiddenItems(cmd, asJSON, itemStatus)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	cmd.Flags().StringVar(&project, "project", "", "Limit to one project's items, in project order")
	cmd.Flags().StringVar(&repo, "repo", "", "Limit to items tagged with this repo (empty string for untagged work)")
	cmd.Flags().StringVar(&itemStatus, "status", "", "One of: "+strings.Join(api.ItemStatuses, ", ")+" (default open)")
	return cmd
}

// validateItemStatus rejects an unknown status here rather than letting the API
// answer 422, so the message names the valid words at the moment they are typed.
func validateItemStatus(cmd *cobra.Command, itemStatus string) error {
	if !cmd.Flags().Changed("status") {
		return nil
	}
	if slices.Contains(api.ItemStatuses, itemStatus) {
		return nil
	}
	return usageError{fmt.Errorf("unknown status %q — one of: %s", itemStatus, strings.Join(api.ItemStatuses, ", "))}
}

// hintHiddenItems says the default hid something, and names the flag that shows
// it. Required by cli-design.md § "A default narrows only where the hidden class
// grows without bound" — the narrowing is allowed precisely because it announces
// itself.
//
// stderr, so a person sees it and --json does not. Silent when a status was
// asked for, because then nothing was hidden the caller did not choose.
// The hint names the command that was actually run, so the scoped reads quote
// themselves back rather than pointing at the unscoped list and losing the
// caller's --project.
// A hint is printed to be typed, and most project names carry spaces, so an
// unquoted one pastes back as several arguments and resolves to nothing.
func shellQuote(s string) string {
	if s != "" && !strings.ContainsAny(s, " \t'\"\\$`") {
		return s
	}
	return "'" + strings.ReplaceAll(s, "'", `'\''`) + "'"
}

func hintHiddenItems(cmd *cobra.Command, asJSON bool, itemStatus string) {
	if asJSON || cmd.Flags().Changed("status") {
		return
	}
	widen := cmd.CommandPath()
	for _, arg := range cmd.Flags().Args() {
		widen += " " + shellQuote(arg)
	}
	if project, err := cmd.Flags().GetString("project"); err == nil && project != "" {
		widen += " --project " + shellQuote(project)
	}
	_, _ = fmt.Fprintf(cmd.ErrOrStderr(), "\nCompleted and archived items are hidden: %s --status all\n", widen)
}

// validateRepoFlag rejects a --repo the registry does not know, on the writes
// only. A typo'd tag is invisible rather than wrong — the item silently drops
// out of every repo view — so it is worth catching at the moment it is typed.
// Reads stay unvalidated: filtering by a name nothing carries is a legitimate
// question with an empty answer.
func validateRepoFlag(cmd *cobra.Command, repo string) error {
	if !cmd.Flags().Changed("repo") {
		return nil
	}
	registry, err := repos.Load(repos.DefaultPath())
	if err != nil {
		return err
	}
	if err := registry.Validate(repo); err != nil {
		return usageError{err}
	}
	return nil
}

// repoFlagValue renders --repo for the API client. Absent is nil (no filter);
// present-but-empty is a pointer to "", which asks for the items that are not
// repo work at all. Collapsing those two would make the untagged work — errands,
// home projects — unreachable.
func repoFlagValue(cmd *cobra.Command, repo string) *string {
	if !cmd.Flags().Changed("repo") {
		return nil
	}
	return &repo
}

// newItemsNextCommand exposes the ordering `icb overview` already computes for
// its project-items section, so a caller that wants only the head of the queue
// does not have to fetch the whole snapshot and re-derive it.
//
// --kind is what makes it useful to `menu next`: a pursuit weighted for making
// things must not resolve to the oldest errand that happens to be filed as a
// project. The filter runs client-side because every item already carries its
// projects, so kind rides along and the alternative would be a query parameter
// that saves no round trip.
func newItemsNextCommand() *cobra.Command {
	var (
		asJSON bool
		kind   string
		repo   string
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "next",
		Short: "The actionable items, in the order to take them",
		Long: "Not completed, not archived, not blocked — oldest first within a project and\n" +
			"interleaved a project at a time, so no single project fills the list. This is\n" +
			"the same ordering `icb overview` shows.",
		Example: "  icb projects items next\n" +
			"  icb projects items next --kind build\n" +
			"  icb projects items next --repo dotfiles\n" +
			"  icb projects items next --kind build --limit 1 --json",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			filter := repoFlagValue(cmd, repo)
			all, err := client.ListItems(cmd.Context(), filter, api.ItemStatusOpen)
			if err != nil {
				return handleAPIError(err)
			}
			// Blocked is deliberately unfiltered: an item is blocked by whatever
			// blocks it, and a blocker in another repo still blocks. Filtering
			// here would present blocked work as actionable.
			blocked, err := client.ListBlockedItems(cmd.Context(), nil)
			if err != nil {
				return handleAPIError(err)
			}
			items := capItems(nextProjectItems(itemsOfKind(all, kind), blocked), limit)
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), items)
			}
			if len(items) == 0 && kind != "" {
				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "No open items in %s projects.\n", kind)
				return nil
			}
			if len(items) == 0 && filter != nil {
				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "No open items for repo %s.\n", *filter)
				return nil
			}
			printItemsTable(cmd.OutOrStdout(), items)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	cmd.Flags().StringVar(&kind, "kind", "", "Only items in projects of this kind: "+strings.Join(api.ProjectKinds, ", "))
	cmd.Flags().StringVar(&repo, "repo", "", "Only items tagged with this repo (empty string for untagged work)")
	cmd.Flags().IntVar(&limit, "limit", 10, "Max items to return (0 for no cap)")
	return cmd
}

// itemsOfKind keeps the items belonging to at least one project of the given
// kind. An empty kind is no filter at all, which is what makes --kind optional
// without a second code path.
func itemsOfKind(items []api.ProjectItem, kind string) []api.ProjectItem {
	if kind == "" {
		return items
	}
	var kept []api.ProjectItem
	for _, item := range items {
		for _, project := range item.Projects {
			if project.Kind == kind {
				kept = append(kept, item)
				break
			}
		}
	}
	return kept
}

func newItemsBlockedCommand() *cobra.Command {
	var (
		asJSON bool
		repo   string
	)
	cmd := &cobra.Command{
		Use:     "blocked",
		Short:   "List items with at least one incomplete dependency",
		Example: "  icb projects items blocked\n  icb projects items blocked --repo homelab",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			filter := repoFlagValue(cmd, repo)
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.ListBlockedItems(cmd.Context(), filter)
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	cmd.Flags().StringVar(&repo, "repo", "", "Only items tagged with this repo (empty string for untagged work)")
	return cmd
}

func newItemsSearchCommand() *cobra.Command {
	var (
		asJSON bool
		repo   string
	)
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search items by title or notes",
		Example: "  icb projects items search kitchen\n  icb projects items search sync --repo todoui",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			filter := repoFlagValue(cmd, repo)
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.SearchItems(cmd.Context(), args[0], filter)
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	cmd.Flags().StringVar(&repo, "repo", "", "Only items tagged with this repo (empty string for untagged work)")
	return cmd
}

func newItemsBlockersCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "blockers <item>",
		Short:   "List the incomplete dependencies blocking an item",
		Example: "  icb projects items blockers 118",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runItemsCollection(cmd, asJSON, func(c *api.Client) ([]api.ProjectItem, error) {
				return c.GetBlockers(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output blockers as JSON to stdout")
	return cmd
}

// runItemsCollection runs a fetch that returns a []ProjectItem and renders it as
// JSON or a table — the shared body of list/blocked/search/blockers.
func runItemsCollection(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.ProjectItem, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	items, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), items)
	}
	printItemsTable(cmd.OutOrStdout(), items)
	return nil
}

// --- Show ---

func newItemsShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <item>",
		Short:   "Show an item with its projects, dependencies, tasks, and blockers",
		Example: "  icb projects items show 118\n  icb projects items show 118 --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			detail, err := client.GetItem(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			tasks, err := client.ListItemTasks(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			blockers, err := client.GetBlockers(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), struct {
					api.ProjectItemDetail
					Tasks    []api.ProjectItemTask `json:"tasks"`
					Blockers []api.ProjectItem     `json:"blockers"`
				}{ProjectItemDetail: detail, Tasks: tasks, Blockers: blockers})
			}
			printItemDetail(cmd.OutOrStdout(), detail, tasks, blockers)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output everything as JSON to stdout")
	return cmd
}

// --- Create / edit ---

// itemCreateFields is the record `items create` builds, in the order it asks.
// The same list drives both doors: unanswered fields become the form, and the
// flags are checked against these validators before anything is sent.
//
// The choices are fetched rather than declared, because a project list and a
// repo registry both change without this file changing. That is also why the
// client is built before the form rather than after it.
func itemCreateFields(ctx context.Context, client *api.Client, made *createdProjects) ([]prompt.Field, error) {
	projects, err := client.ListProjects(ctx, nil, "")
	if err != nil {
		return nil, err
	}
	names := make([]string, 0, len(projects))
	for _, project := range projects {
		names = append(names, project.Name)
	}
	sort.Strings(names)

	registry, err := repos.Load(repos.DefaultPath())
	if err != nil {
		return nil, err
	}
	return []prompt.Field{
		{Key: "title", Label: "Title"},
		{
			Key:      "project",
			Label:    "Project",
			Hint:     "The initiative this belongs to. A repo is the Repo tag below, not a project.",
			Choices:  names,
			Repeat:   true,
			Validate: projectRef(names),
			Escape: &prompt.Escape{
				Trigger: newProjectTrigger,
				Hint:    newProjectTrigger + " makes a new project.",
				Run: func(session prompt.Session) (string, error) {
					name, err := createProjectFromForm(ctx, client, session)
					if name != "" {
						made.add(name)
					}
					return name, err
				},
			},
		},
		{
			Key:      "repo",
			Label:    "Repo",
			Hint:     "The repo this is work on. Leave it empty for work that is not code.",
			Choices:  registry.Names(),
			Optional: true,
			Validate: repoName(registry),
		},
		{Key: "notes", Label: "Notes", Optional: true, Multiline: true},
	}, nil
}

// newProjectTrigger is the answer to Project that makes one instead of picking
// one. A single character keeps it clear of every real name, and no project is
// called "+".
const newProjectTrigger = "+"

// createdProjects is what the Project field's escape committed during a form.
//
// A project is written the moment it is made, and the item it was made for can
// still be abandoned afterwards — by Ctrl-C at Repo or Notes, or by the item's
// own create failing. The project is kept either way, since making it was
// deliberate. What cannot stand is saying nothing: an item-less project is what
// this repo's CLAUDE.md records as the thing that sends later items to the
// wrong place, and the reader has to know one is there to go and use it.
type createdProjects struct{ names []string }

func (c *createdProjects) add(name string) { c.names = append(c.names, name) }

// report names what outlived the form. It prints nothing when the escape was
// never used, which is the ordinary case.
func (c *createdProjects) report(out io.Writer) {
	for _, name := range c.names {
		_, _ = fmt.Fprintf(out, "Project %q was created and kept.\n", name)
	}
}

// createProjectFromForm makes a project without leaving the item being filed,
// and returns its name for the field that ran it.
//
// Filing an item is where the missing project is discovered, and it is the
// worst moment to have to go and make one: the item is half typed and quitting
// to run `projects create` loses it. So the fork is offered where it is found.
//
// An empty name backs out and makes nothing, and says so. Otherwise a "+"
// pressed by mistake would leave only Ctrl-C, and that abandons the item as
// well — and a silent return to Project: reads exactly like a project that was
// created.
//
// A failed create re-asks with all three answers already on their lines. The
// escape exists because quitting to run `projects create` loses the half-typed
// item; a failure path that discards the half-typed project spends the same
// cost one level down.
func createProjectFromForm(ctx context.Context, client *api.Client, session prompt.Session) (string, error) {
	name, err := askProjectName(session)
	if name == "" || err != nil {
		return "", err
	}
	in := api.ProjectCreateInput{Name: name}
	for {
		answers, err := prompt.Form{Fields: newProjectFields(in)}.Run(session)
		if err != nil {
			return "", err
		}
		if description := answers.Get("description"); description != "" {
			in.Description = &description
		}
		if kind := answers.Get("kind"); kind != "" {
			in.Kind = &kind
		}
		project, err := client.CreateProject(ctx, in)
		if err == nil {
			_, _ = fmt.Fprintf(session, "  Created project %q.\n", project.Name)
			return project.Name, nil
		}
		// Reported here rather than returned, so the next pass can put the
		// answers back. handleAPIError is what turns a 401 into the sentence
		// naming `icb auth login`, the same as every other door onto this API.
		_, _ = fmt.Fprintf(session, "  %v\n", handleAPIError(err))
	}
}

// askProjectName asks for the name on its own, so an empty one backs out before
// the description and the kind are asked for a project that will not exist.
func askProjectName(session prompt.Session) (string, error) {
	answers, err := prompt.Form{
		Intro: "New project. Enter on an empty name goes back to picking one.",
		Fields: []prompt.Field{
			{Key: "name", Label: "Name", Optional: true, Validate: boundedProjectName},
		},
	}.Run(session)
	if err != nil {
		return "", err
	}
	if answers.Get("name") == "" {
		_, _ = fmt.Fprintln(session, "  No project made.")
		return "", nil
	}
	return answers.Get("name"), nil
}

// newProjectFields is the rest of the record, with whatever a failed attempt
// already collected as the defaults — so a retry is Enter three times.
func newProjectFields(in api.ProjectCreateInput) []prompt.Field {
	kind := api.ProjectKindBuild
	if in.Kind != nil {
		kind = *in.Kind
	}
	description := ""
	if in.Description != nil {
		description = *in.Description
	}
	return []prompt.Field{
		{
			Key:      "description",
			Label:    "Description",
			Hint:     "What the effort covers. A project without one collects the wrong items later.",
			Default:  description,
			Optional: true,
		},
		{
			Key:      "kind",
			Label:    "Kind",
			Default:  kind,
			Choices:  api.ProjectKinds,
			Validate: prompt.OneOf(api.ProjectKinds),
		},
	}
}

// boundedProjectName is refuseRepoNamedProject as a form validator, so the ban
// reads the same at the prompt as it does behind --name. A form is not a way
// around it.
func boundedProjectName(answer string) (string, error) {
	if err := refuseRepoNamedProject(answer); err != nil {
		return "", err
	}
	return answer, nil
}

// projectRef accepts a project by name, case-insensitively, returning the name
// as the API spells it. A UUID passes straight through: the API resolves either,
// and only the names can be offered as choices.
func projectRef(names []string) func(string) (string, error) {
	byName := prompt.OneOf(names)
	return func(answer string) (string, error) {
		if looksLikeUUID(answer) {
			return answer, nil
		}
		return byName(answer)
	}
}

// looksLikeUUID reports whether s has the 8-4-4-4-12 shape of a project id.
func looksLikeUUID(s string) bool {
	if len(s) != 36 {
		return false
	}
	for i, r := range s {
		if i == 8 || i == 13 || i == 18 || i == 23 {
			if r != '-' {
				return false
			}
			continue
		}
		isHex := (r >= '0' && r <= '9') || (r >= 'a' && r <= 'f') || (r >= 'A' && r <= 'F')
		if !isHex {
			return false
		}
	}
	return true
}

// repoName accepts a registered repo name. A machine whose registry is missing
// accepts anything, which is the policy --repo already followed: an absent
// registry bans nothing.
func repoName(registry *repos.Registry) func(string) (string, error) {
	return func(answer string) (string, error) {
		if err := registry.Validate(answer); err != nil {
			return "", err
		}
		return answer, nil
	}
}

func newItemsCreateCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "create [flags]",
		Short: "Create a new project item in one or more projects",
		Long: "Pass every field as a flag to create in one shot. Leave --title or\n" +
			"--project out at a terminal and the rest are asked for one at a time.\n" +
			"There are more projects and repos than fit on a screen, so neither is\n" +
			"listed up front. Tab prints them, and typing any part of a name first\n" +
			"narrows what it prints; Tab again walks the matches one at a time.\n" +
			"\n" +
			"Answer Project with + to make a new one without leaving the item. It\n" +
			"asks for a name, a description and a kind, then goes on filing.\n" +
			"\n" +
			"Project repeats until you press Enter on an empty one, so an item can\n" +
			"join several. Notes take as many lines as you want and end on a blank\n" +
			"one. An answer the field rejects comes back for editing and nothing\n" +
			"already entered is lost. Ctrl-C abandons the item.",
		Example: "  icb projects items create\n" +
			"  icb projects items create --title \"Ship the CLI\" --project todoui",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			answers := flagAnswers(cmd, "title", "project", "repo", "notes")
			missing := missingFlags(answers, "title", "project")
			// Ahead of the client, so a caller that cannot be asked is told
			// which flag it left out rather than that the API is unreachable.
			if len(missing) > 0 && !interactive(cmd) {
				return usageError{fmt.Errorf("%s required — pass them, or run from a terminal to be asked",
					strings.Join(missing, " and "))}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			made := &createdProjects{}
			fields, err := itemCreateFields(cmd.Context(), client, made)
			if err != nil {
				return handleAPIError(err)
			}
			if err := validateAnswers(answers, fields); err != nil {
				return usageError{err}
			}
			if len(missing) > 0 {
				asked, err := runForm(cmd, prompt.Form{
					Intro:  "Creating a project item. Ctrl-C to abandon it.",
					Fields: unanswered(fields, answers),
				})
				if errors.Is(err, errAborted) {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nAborted.")
					made.report(cmd.ErrOrStderr())
					return nil
				}
				if err != nil {
					made.report(cmd.ErrOrStderr())
					return err
				}
				answers.Merge(asked)
			}
			in := api.ProjectItemCreateInput{
				Title:      answers.Get("title"),
				ProjectIDs: answers.All("project"),
			}
			if answers.Has("notes") {
				notes := answers.Get("notes")
				in.Notes = &notes
			}
			if answers.Has("repo") {
				repo := answers.Get("repo")
				in.Repo = &repo
			}
			item, err := client.CreateItem(cmd.Context(), in)
			if err != nil {
				made.report(cmd.ErrOrStderr())
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), item)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created item %q (%d)\n", item.Title, item.Number)
			return nil
		},
	}
	cmd.Flags().String("title", "", "Item title (asked for when omitted)")
	cmd.Flags().String("notes", "", "Markdown notes for the item")
	cmd.Flags().String("repo", "", "Repo this item is work on, by registry name (optional)")
	cmd.Flags().StringArray("project", nil, "Project name or id to add the item to (repeatable; asked for when omitted)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created item as JSON to stdout")
	return cmd
}

func newItemsEditCommand() *cobra.Command {
	var (
		title  string
		notes  string
		repo   string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "edit <item> [flags]",
		Short:   "Change an item's title, notes, or repo",
		Long:    "Update only the fields whose flags you pass. Use complete/reopen and\narchive/unarchive for those state changes.\n\nPass --repo \"\" to unlink an item from its repo.",
		Example: "  icb projects items edit 118 --title \"New title\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ProjectItemUpdateInput{}
			if f.Changed("title") {
				in.Title = &title
			}
			if f.Changed("notes") {
				in.Notes = &notes
			}
			if f.Changed("repo") {
				if err := validateRepoFlag(cmd, repo); err != nil {
					return err
				}
				in.Repo = &repo
			}
			if in == (api.ProjectItemUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass --title, --notes, and/or --repo")}
			}
			return runItemUpdate(cmd, args[0], in, asJSON, "Updated")
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "New item title")
	cmd.Flags().StringVar(&notes, "notes", "", "New markdown notes")
	cmd.Flags().StringVar(&repo, "repo", "", "Repo this item is work on, by registry name (empty string unlinks)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

// newItemsCompletionCommand builds the complete/reopen pair — a PATCH of the
// completed flag. Completing is refused by the API (400) while tasks remain.
func newItemsCompletionCommand(verb, short string, completed bool) *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     verb + " <item>",
		Short:   short,
		Example: "  icb projects items " + verb + " 118",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			flag := completed
			return runItemUpdate(cmd, args[0], api.ProjectItemUpdateInput{Completed: &flag}, asJSON, "Updated")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

// newItemsArchiveCommand builds the archive/unarchive pair — a PATCH of the
// archived flag.
func newItemsArchiveCommand(verb, short string, archived bool) *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     verb + " <item>",
		Short:   short,
		Example: "  icb projects items " + verb + " 118",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			flag := archived
			return runItemUpdate(cmd, args[0], api.ProjectItemUpdateInput{Archived: &flag}, asJSON, "Updated")
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

// runItemUpdate applies a PATCH and renders the result — shared by edit,
// complete/reopen, and archive/unarchive.
func runItemUpdate(cmd *cobra.Command, id string, in api.ProjectItemUpdateInput, asJSON bool, verb string) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	item, err := client.UpdateItem(cmd.Context(), id, in)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), item)
	}
	_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s item %q → %s (%d)\n", verb, item.Title, flatItemStatus(item), item.Number)
	return nil
}

func newItemsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <item>",
		Short:   "Delete a project item",
		Long:    "Permanently delete an item and its tasks. Prompts for confirmation unless --yes.",
		Example: "  icb projects items delete 118 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.GetItem(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd,
					fmt.Sprintf("Delete item %q? This cannot be undone.", item.Title))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteItem(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted item %q (%d)\n", item.Title, item.Number)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func newItemsReorderCommand() *cobra.Command {
	var (
		project  string
		position int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "reorder <item> --project <project> --position <n>",
		Short:   "Move an item to a new position within a project",
		Example: "  icb projects items reorder 118 --project todoui --position 2",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if project == "" {
				return usageError{fmt.Errorf("--project is required")}
			}
			if !cmd.Flags().Changed("position") {
				return usageError{fmt.Errorf("--position is required")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.ReorderItem(cmd.Context(), args[0], api.ProjectItemReorderInput{ProjectID: project, Position: position})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), item)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Moved item %q to position %d (%d)\n", item.Title, item.Position, item.Number)
			return nil
		},
	}
	cmd.Flags().StringVar(&project, "project", "", "Project name or id the item is being reordered within (required)")
	cmd.Flags().IntVar(&position, "position", 0, "New position (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the item as JSON to stdout")
	return cmd
}

// --- Membership ---

func newItemsAddProjectCommand() *cobra.Command {
	var (
		project string
		asJSON  bool
	)
	cmd := &cobra.Command{
		Use:     "add-project <item> --project <project>",
		Short:   "Add an item to another project",
		Example: "  icb projects items add-project 118 --project todoui",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if project == "" {
				return usageError{fmt.Errorf("--project is required")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			p, err := client.AddItemToProject(cmd.Context(), args[0], api.ProjectMembershipInput{ProjectID: project})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), p)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Added item %s to project %q (%s)\n", args[0], p.Name, p.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&project, "project", "", "Project name or id to add the item to (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the project as JSON to stdout")
	return cmd
}

func newItemsRemoveProjectCommand() *cobra.Command {
	var (
		project string
		yes     bool
	)
	cmd := &cobra.Command{
		Use:     "remove-project <item> --project <project>",
		Short:   "Remove an item from a project",
		Long:    "Remove an item from a project. An item always belongs to at least one\nproject, so removing it from its last one is refused — delete the item instead.",
		Example: "  icb projects items remove-project 118 --project todoui",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if project == "" {
				return usageError{fmt.Errorf("--project is required")}
			}
			if !yes {
				ok, err := confirm(cmd,
					fmt.Sprintf("Remove item %s from project %s?", args[0], project))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if err := client.RemoveItemFromProject(cmd.Context(), args[0], project); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Removed item %s from project %s\n", args[0], project)
			return nil
		},
	}
	cmd.Flags().StringVar(&project, "project", "", "Project name or id to remove the item from (required)")
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// --- Dependencies ---

func newItemsAddDependencyCommand() *cobra.Command {
	var (
		dependsOn string
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "add-dependency <item> --depends-on <other-item>",
		Short:   "Record that an item depends on another item",
		Long:    "An item cannot depend on itself, and a dependency that would close a cycle\nis refused.",
		Example: "  icb projects items add-dependency 118 --depends-on 42",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if dependsOn == "" {
				return usageError{fmt.Errorf("--depends-on is required")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			detail, err := client.AddDependency(cmd.Context(), args[0], api.DependencyInput{DependsOnID: dependsOn})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), detail)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Item %q now depends on %s (%d total dependencies)\n", detail.Title, dependsOn, len(detail.DependencyIDs))
			return nil
		},
	}
	cmd.Flags().StringVar(&dependsOn, "depends-on", "", "Item number or id this item depends on (required)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the item detail as JSON to stdout")
	return cmd
}

func newItemsRemoveDependencyCommand() *cobra.Command {
	var (
		dependsOn string
		yes       bool
	)
	cmd := &cobra.Command{
		Use:     "remove-dependency <item> --depends-on <other-item>",
		Short:   "Remove a dependency edge between two items",
		Example: "  icb projects items remove-dependency 118 --depends-on 42",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if dependsOn == "" {
				return usageError{fmt.Errorf("--depends-on is required")}
			}
			if !yes {
				ok, err := confirm(cmd,
					fmt.Sprintf("Remove dependency %s → %s?", args[0], dependsOn))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if err := client.RemoveDependency(cmd.Context(), args[0], dependsOn); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Removed dependency %s → %s\n", args[0], dependsOn)
			return nil
		},
	}
	cmd.Flags().StringVar(&dependsOn, "depends-on", "", "Dependency item number or id to remove (required)")
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// --- Tasks (sub-verbs on an item) ---

func newItemsTasksCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "tasks <item>",
		Short:   "List an item's tasks",
		Example: "  icb projects items tasks 118",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			tasks, err := client.ListItemTasks(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), tasks)
			}
			printTasksTable(cmd.OutOrStdout(), tasks)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output tasks as JSON to stdout")
	return cmd
}

func newItemsAddTaskCommand() *cobra.Command {
	var (
		title    string
		position int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "add-task <item> --title <title>",
		Short:   "Add a task to an item",
		Example: "  icb projects items add-task 118 --title \"write tests\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if title == "" {
				return usageError{fmt.Errorf("--title is required")}
			}
			in := api.ProjectItemTaskCreateInput{Title: title}
			if cmd.Flags().Changed("position") {
				in.Position = &position
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			task, err := client.CreateItemTask(cmd.Context(), args[0], in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), task)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Added task %q (%s)\n", task.Title, task.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "Task title (required)")
	cmd.Flags().IntVar(&position, "position", 0, "Task position within the item")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created task as JSON to stdout")
	return cmd
}

func newItemsCompleteTaskCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "complete-task <item> <task-id>",
		Short:   "Mark an item's task completed",
		Example: "  icb projects items complete-task 118 018g...",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			completed := true
			return runTaskUpdate(cmd, args[0], args[1], api.ProjectItemTaskUpdateInput{Completed: &completed}, asJSON)
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated task as JSON to stdout")
	return cmd
}

func newItemsEditTaskCommand() *cobra.Command {
	var (
		title     string
		completed bool
		position  int
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "edit-task <item> <task-id> [flags]",
		Short:   "Change a task's title, completion, or position",
		Example: "  icb projects items edit-task 118 018g... --title \"new\" --completed",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ProjectItemTaskUpdateInput{}
			if f.Changed("title") {
				in.Title = &title
			}
			if f.Changed("completed") {
				in.Completed = &completed
			}
			if f.Changed("position") {
				in.Position = &position
			}
			if in == (api.ProjectItemTaskUpdateInput{}) {
				return usageError{fmt.Errorf("nothing to change — pass --title, --completed, and/or --position")}
			}
			return runTaskUpdate(cmd, args[0], args[1], in, asJSON)
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "New task title")
	cmd.Flags().BoolVar(&completed, "completed", false, "Set completion state")
	cmd.Flags().IntVar(&position, "position", 0, "New position")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated task as JSON to stdout")
	return cmd
}

// runTaskUpdate applies a PATCH to a task and renders it — shared by
// complete-task and edit-task.
func runTaskUpdate(cmd *cobra.Command, itemID, taskID string, in api.ProjectItemTaskUpdateInput, asJSON bool) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	task, err := client.UpdateItemTask(cmd.Context(), itemID, taskID, in)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), task)
	}
	_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated task %q → %s (%s)\n", task.Title, taskState(task), task.ID)
	return nil
}

func newItemsRemoveTaskCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "remove-task <item> <task-id>",
		Short:   "Delete a task from an item",
		Example: "  icb projects items remove-task 118 018g... --yes",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if !yes {
				ok, err := confirm(cmd,
					fmt.Sprintf("Delete task %s?", args[1]))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if err := client.DeleteItemTask(cmd.Context(), args[0], args[1]); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted task %s\n", args[1])
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// --- Rendering ---

func printItemsTable(out io.Writer, items []api.ProjectItem) {
	if len(items) == 0 {
		_, _ = fmt.Fprintln(out, "No items.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "STATUS\tTITLE\tID")
	for _, it := range items {
		_, _ = fmt.Fprintf(tw, "%s\t%s\t%d\n", flatItemStatus(it), it.Title, it.Number)
	}
	_ = tw.Flush()
}

func printItemDetail(out io.Writer, d api.ProjectItemDetail, tasks []api.ProjectItemTask, blockers []api.ProjectItem) {
	_, _ = fmt.Fprintf(out, "%s\n", d.Title)
	_, _ = fmt.Fprintf(out, "  id:      %d\n", d.Number)
	_, _ = fmt.Fprintf(out, "  status:  %s\n", detailStatus(d))
	if r := strValue(d.Repo); r != "" {
		_, _ = fmt.Fprintf(out, "  repo:    %s\n", r)
	}
	if n := strValue(d.Notes); n != "" {
		_, _ = fmt.Fprintf(out, "  notes:   %s\n", n)
	}

	projectNames := make([]string, 0, len(d.Projects))
	for _, p := range d.Projects {
		projectNames = append(projectNames, p.Name)
	}
	_, _ = fmt.Fprintf(out, "  projects: %s\n", orNone(strings.Join(projectNames, ", ")))
	_, _ = fmt.Fprintf(out, "  depends on: %d item(s)\n", len(d.DependencyIDs))

	_, _ = fmt.Fprintf(out, "\nTasks (%d):\n", len(tasks))
	if len(tasks) == 0 {
		_, _ = fmt.Fprintln(out, "  (none)")
	} else {
		printTasksTable(out, tasks)
	}

	if len(blockers) > 0 {
		_, _ = fmt.Fprintf(out, "\nBlocked by %d incomplete item(s):\n", len(blockers))
		printItemsTable(out, blockers)
	}
}

func printTasksTable(out io.Writer, tasks []api.ProjectItemTask) {
	if len(tasks) == 0 {
		_, _ = fmt.Fprintln(out, "No tasks.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "  #\tSTATUS\tTITLE\tID")
	for _, t := range tasks {
		_, _ = fmt.Fprintf(tw, "  %d\t%s\t%s\t%s\n", t.Position, taskState(t), t.Title, t.ID)
	}
	_ = tw.Flush()
}

// itemStatusWord renders the two booleans as the word --status accepts, so what
// a row shows is what you can filter on. Archived beats completed, which is the
// precedence the API applies and the item counts partition by.
func itemStatusWord(archived, completed bool) string {
	switch {
	case archived:
		return api.ItemStatusArchived
	case completed:
		return api.ItemStatusCompleted
	default:
		return api.ItemStatusOpen
	}
}

func flatItemStatus(it api.ProjectItem) string { return itemStatusWord(it.Archived, it.Completed) }

func detailStatus(d api.ProjectItemDetail) string { return itemStatusWord(d.Archived, d.Completed) }

// A task has no archived state, so it is the same vocabulary minus one word.
func taskState(t api.ProjectItemTask) string { return itemStatusWord(false, t.Completed) }

// orNone renders an empty string as "(none)" for list-style detail fields.
func orNone(s string) string {
	if s == "" {
		return "(none)"
	}
	return s
}
