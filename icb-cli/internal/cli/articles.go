package cli

import (
	"fmt"
	"io"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newArticlesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "articles",
		Short: "List, inspect, search, and manage your saved articles",
		Long:  "Work with the reading list in the ichrisbirch API as yourself. Requires a\nlogged-in session (`icb auth login`).",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(
		newArticlesListCommand(),
		newArticlesViewCommand(),
		newArticlesCurrentCommand(),
		newArticlesSearchCommand(),
		newArticlesCreateCommand(),
		newArticlesEditCommand(),
		newArticlesReadCommand(),
		newArticlesDeleteCommand(),
	)
	return cmd
}

func newArticlesListCommand() *cobra.Command {
	var (
		favorites bool
		archived  bool
		unread    bool
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List articles",
		Long: "List articles ordered by title. The filters are tri-state: pass --favorites\n" +
			"for favorites due for re-read, --favorites=false to exclude favorites, or\n" +
			"omit it to ignore the filter. Same for --archived and --unread.",
		Example: "  icb articles list\n  icb articles list --unread\n  icb articles list --archived=false",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runArticleList(cmd, asJSON, func(c *api.Client) ([]api.Article, error) {
				return c.ListArticles(cmd.Context(),
					boolFlagPtr(cmd, "favorites"), boolFlagPtr(cmd, "archived"), boolFlagPtr(cmd, "unread"))
			})
		},
	}
	cmd.Flags().BoolVar(&favorites, "favorites", false, "Filter by favorite status (favorites due for re-read)")
	cmd.Flags().BoolVar(&archived, "archived", false, "Filter by archived status")
	cmd.Flags().BoolVar(&unread, "unread", false, "Filter by never-read status")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output articles as JSON to stdout")
	return cmd
}

func newArticlesSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search articles by tag",
		Long:    "Comma-separated terms are matched independently (\"python,databases\" finds\narticles tagged with either).",
		Example: "  icb articles search databases\n  icb articles search \"python,systems\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runArticleList(cmd, asJSON, func(c *api.Client) ([]api.Article, error) {
				return c.SearchArticles(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output articles as JSON to stdout")
	return cmd
}

func newArticlesViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <article-id>",
		Short:   "Show a single article",
		Example: "  icb articles view 42",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("article id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			article, err := client.GetArticle(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), article)
			}
			printArticleDetail(cmd.OutOrStdout(), article)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the article as JSON to stdout")
	return cmd
}

func newArticlesCurrentCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "current",
		Short:   "Show the current article (the one being read)",
		Example: "  icb articles current",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			article, err := client.GetCurrentArticle(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), article)
			}
			if article == nil {
				fmt.Fprintln(cmd.OutOrStdout(), "No current article.")
				return nil
			}
			printArticleDetail(cmd.OutOrStdout(), *article)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the article (or null) as JSON to stdout")
	return cmd
}

func newArticlesCreateCommand() *cobra.Command {
	var (
		articleURL string
		notes      string
		asJSON     bool
	)
	cmd := &cobra.Command{
		Use:   "create --url <url> [--notes <notes>]",
		Short: "Save an article from a URL",
		Long:  "Fetch the URL and AI-summarize it into a new article (title, summary, tags\nare generated server-side).",
		Example: "  icb articles create --url https://example.com/post\n" +
			"  icb articles create --url https://example.com/post --notes \"for the DB deep-dive\"",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if articleURL == "" {
				return usageError{fmt.Errorf("--url is required")}
			}
			in := api.ArticleCreateFromURLInput{URL: articleURL}
			in.Notes = strFlag(cmd.Flags(), "notes", &notes)

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			article, err := client.CreateArticleFromURL(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), article)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Saved article %q (id %d)\n", article.Title, article.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&articleURL, "url", "", "URL of the article to save")
	cmd.Flags().StringVar(&notes, "notes", "", "Notes to attach to the article")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created article as JSON to stdout")
	return cmd
}

func newArticlesEditCommand() *cobra.Command {
	var (
		title      string
		tags       []string
		summary    string
		notes      string
		favorite   bool
		current    bool
		archived   bool
		lastRead   string
		readCount  int
		reviewDays int
		asJSON     bool
	)
	cmd := &cobra.Command{
		Use:     "edit <article-id> [flags]",
		Short:   "Change fields on an existing article",
		Long:    "Update only the fields whose flags you pass.",
		Example: "  icb articles edit 42 --favorite --review-days 30\n  icb articles edit 42 --tag python --tag databases",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("article id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.ArticleUpdateInput{}
			in.Title = strFlag(f, "title", &title)
			if f.Changed("tag") {
				in.Tags = tags
			}
			in.Summary = strFlag(f, "summary", &summary)
			in.Notes = strFlag(f, "notes", &notes)
			in.IsFavorite = boolFlagPtr(cmd, "favorite")
			in.IsCurrent = boolFlagPtr(cmd, "current")
			in.IsArchived = boolFlagPtr(cmd, "archived")
			in.LastReadDate = strFlag(f, "last-read", &lastRead)
			in.ReadCount = intFlag(f, "read-count", &readCount)
			in.ReviewDays = intFlag(f, "review-days", &reviewDays)

			if isEmptyArticleUpdate(in) {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag")}
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			article, err := client.UpdateArticle(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), article)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Updated article %q (id %d)\n", article.Title, article.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&title, "title", "", "Article title")
	cmd.Flags().StringArrayVar(&tags, "tag", nil, "Tag (repeatable; replaces the tag list)")
	cmd.Flags().StringVar(&summary, "summary", "", "Summary text")
	cmd.Flags().StringVar(&notes, "notes", "", "Notes")
	cmd.Flags().BoolVar(&favorite, "favorite", false, "Mark as favorite (--favorite or --favorite=false)")
	cmd.Flags().BoolVar(&current, "current", false, "Mark as the current article (--current or --current=false)")
	cmd.Flags().BoolVar(&archived, "archived", false, "Mark as archived (--archived or --archived=false)")
	cmd.Flags().StringVar(&lastRead, "last-read", "", "Last-read date (ISO, e.g. 2026-07-24T09:00:00)")
	cmd.Flags().IntVar(&readCount, "read-count", 0, "Read count")
	cmd.Flags().IntVar(&reviewDays, "review-days", 0, "Days between re-reads for a favorite")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated article as JSON to stdout")
	return cmd
}

func newArticlesReadCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "read <article-id>",
		Short:   "Mark an article read (archive it, bump read count, stamp now)",
		Long:    "Fetch the article for its current read count, then archive it, increment the\nread count, and set the last-read date to now.",
		Example: "  icb articles read 42",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("article id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			article, err := client.GetArticle(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			archived := true
			nextCount := article.ReadCount + 1
			now := time.Now().Format(time.RFC3339)
			updated, err := client.UpdateArticle(cmd.Context(), id, api.ArticleUpdateInput{
				IsArchived:   &archived,
				ReadCount:    &nextCount,
				LastReadDate: &now,
			})
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), updated)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Marked article %q read (id %d, read %d×)\n",
				updated.Title, updated.ID, updated.ReadCount)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated article as JSON to stdout")
	return cmd
}

func newArticlesDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <article-id>",
		Short:   "Delete an article",
		Example: "  icb articles delete 42 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("article id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			article, err := client.GetArticle(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete article %q (id %d)?", article.Title, article.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteArticle(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted article %q (id %d)\n", article.Title, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// isEmptyArticleUpdate reports whether no fields were set on a partial update.
func isEmptyArticleUpdate(in api.ArticleUpdateInput) bool {
	return in.Title == nil && in.Tags == nil && in.Summary == nil && in.Notes == nil &&
		in.IsFavorite == nil && in.IsCurrent == nil && in.IsArchived == nil &&
		in.LastReadDate == nil && in.ReadCount == nil && in.ReviewDays == nil
}

func runArticleList(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.Article, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	articles, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), articles)
	}
	printArticlesTable(cmd.OutOrStdout(), articles)
	return nil
}

func printArticlesTable(out io.Writer, articles []api.Article) {
	if len(articles) == 0 {
		fmt.Fprintln(out, "No articles.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tFAV\tARCH\tREADS\tTITLE\tTAGS")
	for _, a := range articles {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%d\t%s\t%s\n",
			a.ID, yesNo(a.IsFavorite), yesNo(a.IsArchived), a.ReadCount, a.Title, strings.Join(a.Tags, ", "))
	}
	_ = tw.Flush()
}

func printArticleDetail(out io.Writer, a api.Article) {
	fmt.Fprintf(out, "%s\n", a.Title)
	fmt.Fprintf(out, "  id:        %d\n", a.ID)
	fmt.Fprintf(out, "  url:       %s\n", a.URL)
	fmt.Fprintf(out, "  tags:      %s\n", orNone(strings.Join(a.Tags, ", ")))
	fmt.Fprintf(out, "  favorite:  %s\n", yesNo(a.IsFavorite))
	fmt.Fprintf(out, "  current:   %s\n", yesNo(a.IsCurrent))
	fmt.Fprintf(out, "  archived:  %s\n", yesNo(a.IsArchived))
	fmt.Fprintf(out, "  reads:     %d\n", a.ReadCount)
	fmt.Fprintf(out, "  saved:     %s\n", a.SaveDate.Format("2006-01-02"))
	if a.LastReadDate != nil {
		fmt.Fprintf(out, "  last read: %s\n", a.LastReadDate.Format("2006-01-02"))
	}
	if a.ReviewDays != nil {
		fmt.Fprintf(out, "  review:    every %d days\n", *a.ReviewDays)
	}
	if a.Summary != "" {
		fmt.Fprintf(out, "  summary:   %s\n", a.Summary)
	}
	if s := strValue(a.Notes); s != "" {
		fmt.Fprintf(out, "  notes:     %s\n", s)
	}
}
