package cli

import (
	"fmt"
	"io"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"

	"ichrisbirch/cli/internal/api"
)

// bookFlagVars holds the flag targets shared by `books create` and `books edit`.
type bookFlagVars struct {
	title, author, isbn, goodreadsURL             string
	location, notes, ownership, progress          string
	review, rejectReason                          string
	tags                                          []string
	priority, rating                              int
	purchasePrice, sellPrice                      float64
	purchaseDate, sellDate, readStart, readFinish string
}

func newBooksCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "books",
		Short: "List, inspect, search, and manage your books",
		Long:  "Work with the book catalog in the ichrisbirch API as yourself. Requires a\nlogged-in session (`icb auth login`).",
		RunE:  requireSubcommand,
	}
	cmd.AddCommand(
		newBooksListCommand(),
		newBooksViewCommand(),
		newBooksISBNCommand(),
		newBooksSearchCommand(),
		newBooksCreateCommand(),
		newBooksEditCommand(),
		newBooksDeleteCommand(),
	)
	return cmd
}

func newBooksListCommand() *cobra.Command {
	var (
		ownership string
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List books by priority",
		Example: "  icb books list\n  icb books list --ownership owned",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runBookList(cmd, asJSON, func(c *api.Client) ([]api.Book, error) {
				return c.ListBooks(cmd.Context(), ownership)
			})
		},
	}
	cmd.Flags().StringVar(&ownership, "ownership", "", "Filter by ownership (e.g. owned, want, rejected)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output books as JSON to stdout")
	return cmd
}

func newBooksSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search books by title, author, or tags",
		Long:    "Comma-separated terms preserve phrases (\"shadow work,Jung\"); otherwise\nwhitespace splits into keywords matched against any field.",
		Example: "  icb books search Kleppmann\n  icb books search \"shadow work,Jung\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runBookList(cmd, asJSON, func(c *api.Client) ([]api.Book, error) {
				return c.SearchBooks(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output books as JSON to stdout")
	return cmd
}

func newBooksViewCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "view <book-id>",
		Short:   "Show a single book",
		Example: "  icb books view 140",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("book id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			book, err := client.GetBook(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), book)
			}
			printBookDetail(cmd.OutOrStdout(), book)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the book as JSON to stdout")
	return cmd
}

func newBooksISBNCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "isbn <isbn>",
		Short:   "Look up a book by ISBN",
		Example: "  icb books isbn 9781449373320",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			book, err := client.GetBookByISBN(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), book)
			}
			printBookDetail(cmd.OutOrStdout(), book)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the book as JSON to stdout")
	return cmd
}

func newBooksCreateCommand() *cobra.Command {
	var (
		v      bookFlagVars
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "create --title <title> --author <author> --tag <tag> [flags]",
		Short:   "Create a new book",
		Example: "  icb books create --title \"DDIA\" --author Kleppmann --tag databases --tag systems",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			f := cmd.Flags()
			if !f.Changed("title") || !f.Changed("author") {
				return usageError{fmt.Errorf("--title and --author are required")}
			}
			if len(v.tags) == 0 {
				return usageError{fmt.Errorf("at least one --tag is required")}
			}
			in := api.BookCreateInput{Title: v.title, Author: v.author, Tags: v.tags}
			in.ISBN = strFlag(f, "isbn", &v.isbn)
			in.GoodreadsURL = strFlag(f, "goodreads-url", &v.goodreadsURL)
			in.Priority = intFlag(f, "priority", &v.priority)
			in.Rating = intFlag(f, "rating", &v.rating)
			in.Location = strFlag(f, "location", &v.location)
			in.Notes = strFlag(f, "notes", &v.notes)
			in.Ownership = strFlag(f, "ownership", &v.ownership)
			in.Progress = strFlag(f, "progress", &v.progress)
			in.Review = strFlag(f, "review", &v.review)
			in.RejectReason = strFlag(f, "reject-reason", &v.rejectReason)
			in.PurchaseDate = strFlag(f, "purchase-date", &v.purchaseDate)
			in.PurchasePrice = floatFlag(f, "purchase-price", &v.purchasePrice)
			in.SellDate = strFlag(f, "sell-date", &v.sellDate)
			in.SellPrice = floatFlag(f, "sell-price", &v.sellPrice)
			in.ReadStartDate = strFlag(f, "read-start", &v.readStart)
			in.ReadFinishDate = strFlag(f, "read-finish", &v.readFinish)

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			book, err := client.CreateBook(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), book)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Created book %q by %s (id %d)\n", book.Title, book.Author, book.ID)
			return nil
		},
	}
	addBookFlags(cmd, &v)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created book as JSON to stdout")
	return cmd
}

func newBooksEditCommand() *cobra.Command {
	var (
		v      bookFlagVars
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:     "edit <book-id> [flags]",
		Short:   "Change fields on an existing book",
		Long:    "Update only the fields whose flags you pass.",
		Example: "  icb books edit 140 --progress reading --read-start 2026-07-01",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("book id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.BookUpdateInput{}
			in.Title = strFlag(f, "title", &v.title)
			in.Author = strFlag(f, "author", &v.author)
			if f.Changed("tag") {
				in.Tags = v.tags
			}
			in.ISBN = strFlag(f, "isbn", &v.isbn)
			in.GoodreadsURL = strFlag(f, "goodreads-url", &v.goodreadsURL)
			in.Priority = intFlag(f, "priority", &v.priority)
			in.Rating = intFlag(f, "rating", &v.rating)
			in.Location = strFlag(f, "location", &v.location)
			in.Notes = strFlag(f, "notes", &v.notes)
			in.Ownership = strFlag(f, "ownership", &v.ownership)
			in.Progress = strFlag(f, "progress", &v.progress)
			in.Review = strFlag(f, "review", &v.review)
			in.RejectReason = strFlag(f, "reject-reason", &v.rejectReason)
			in.PurchaseDate = strFlag(f, "purchase-date", &v.purchaseDate)
			in.PurchasePrice = floatFlag(f, "purchase-price", &v.purchasePrice)
			in.SellDate = strFlag(f, "sell-date", &v.sellDate)
			in.SellPrice = floatFlag(f, "sell-price", &v.sellPrice)
			in.ReadStartDate = strFlag(f, "read-start", &v.readStart)
			in.ReadFinishDate = strFlag(f, "read-finish", &v.readFinish)

			if isEmptyBookUpdate(in) {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag")}
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			book, err := client.UpdateBook(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), book)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Updated book %q (id %d)\n", book.Title, book.ID)
			return nil
		},
	}
	addBookFlags(cmd, &v)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated book as JSON to stdout")
	return cmd
}

func newBooksDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <book-id>",
		Short:   "Delete a book",
		Example: "  icb books delete 140 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("book id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			book, err := client.GetBook(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete book %q by %s (id %d)?", book.Title, book.Author, book.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteBook(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted book %q (id %d)\n", book.Title, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// addBookFlags registers the shared create/edit flags on cmd.
func addBookFlags(cmd *cobra.Command, v *bookFlagVars) {
	f := cmd.Flags()
	f.StringVar(&v.title, "title", "", "Book title")
	f.StringVar(&v.author, "author", "", "Author")
	f.StringArrayVar(&v.tags, "tag", nil, "Tag (repeatable; at least one on create)")
	f.StringVar(&v.isbn, "isbn", "", "ISBN")
	f.StringVar(&v.goodreadsURL, "goodreads-url", "", "Goodreads URL")
	f.IntVar(&v.priority, "priority", 0, "Reading priority")
	f.IntVar(&v.rating, "rating", 0, "Rating")
	f.StringVar(&v.location, "location", "", "Physical/shelf location")
	f.StringVar(&v.notes, "notes", "", "Notes")
	f.StringVar(&v.ownership, "ownership", "", "Ownership (e.g. owned, want, rejected)")
	f.StringVar(&v.progress, "progress", "", "Progress (e.g. unread, reading, read)")
	f.StringVar(&v.review, "review", "", "Review text")
	f.StringVar(&v.rejectReason, "reject-reason", "", "Reason for rejecting the book")
	f.StringVar(&v.purchaseDate, "purchase-date", "", "Purchase date")
	f.Float64Var(&v.purchasePrice, "purchase-price", 0, "Purchase price")
	f.StringVar(&v.sellDate, "sell-date", "", "Sell date")
	f.Float64Var(&v.sellPrice, "sell-price", 0, "Sell price")
	f.StringVar(&v.readStart, "read-start", "", "Reading start date")
	f.StringVar(&v.readFinish, "read-finish", "", "Reading finish date")
}

// isEmptyBookUpdate reports whether no fields were set on a partial update.
func isEmptyBookUpdate(in api.BookUpdateInput) bool {
	return in.Title == nil && in.Author == nil && in.Tags == nil && in.ISBN == nil &&
		in.GoodreadsURL == nil && in.Priority == nil && in.Rating == nil && in.Location == nil &&
		in.Notes == nil && in.Ownership == nil && in.Progress == nil && in.Review == nil &&
		in.RejectReason == nil && in.PurchaseDate == nil && in.PurchasePrice == nil &&
		in.SellDate == nil && in.SellPrice == nil && in.ReadStartDate == nil && in.ReadFinishDate == nil
}

// strFlag / intFlag / floatFlag return a pointer to the flag's value if the user
// set it, else nil — the omitempty partial-update idiom, factored for the many
// optional book fields.
func strFlag(f *pflag.FlagSet, name string, v *string) *string {
	if f.Changed(name) {
		return v
	}
	return nil
}

func intFlag(f *pflag.FlagSet, name string, v *int) *int {
	if f.Changed(name) {
		return v
	}
	return nil
}

func floatFlag(f *pflag.FlagSet, name string, v *float64) *float64 {
	if f.Changed(name) {
		return v
	}
	return nil
}

func runBookList(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.Book, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	books, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), books)
	}
	printBooksTable(cmd.OutOrStdout(), books)
	return nil
}

func printBooksTable(out io.Writer, books []api.Book) {
	if len(books) == 0 {
		fmt.Fprintln(out, "No books.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tPROGRESS\tOWNED\tRATING\tTITLE\tAUTHOR")
	for _, b := range books {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%s\t%s\t%s\n", b.ID, b.Progress, b.Ownership, intOrDash(b.Rating), b.Title, b.Author)
	}
	_ = tw.Flush()
}

func printBookDetail(out io.Writer, b api.Book) {
	fmt.Fprintf(out, "%s\n", b.Title)
	fmt.Fprintf(out, "  id:       %d\n", b.ID)
	fmt.Fprintf(out, "  author:   %s\n", b.Author)
	fmt.Fprintf(out, "  tags:     %s\n", orNone(strings.Join(b.Tags, ", ")))
	fmt.Fprintf(out, "  ownership: %s\n", b.Ownership)
	fmt.Fprintf(out, "  progress: %s\n", b.Progress)
	if b.Rating != nil {
		fmt.Fprintf(out, "  rating:   %d\n", *b.Rating)
	}
	if b.Priority != nil {
		fmt.Fprintf(out, "  priority: %d\n", *b.Priority)
	}
	if s := strValue(b.ISBN); s != "" {
		fmt.Fprintf(out, "  isbn:     %s\n", s)
	}
	if s := strValue(b.Location); s != "" {
		fmt.Fprintf(out, "  location: %s\n", s)
	}
	if b.ReadStartDate != nil {
		fmt.Fprintf(out, "  reading:  started %s\n", b.ReadStartDate.Format("2006-01-02"))
	}
	if b.ReadFinishDate != nil {
		fmt.Fprintf(out, "  finished: %s\n", b.ReadFinishDate.Format("2006-01-02"))
	}
	if s := strValue(b.Notes); s != "" {
		fmt.Fprintf(out, "  notes:    %s\n", s)
	}
	if s := strValue(b.Review); s != "" {
		fmt.Fprintf(out, "  review:   %s\n", s)
	}
}

// intOrDash renders a nullable int as an em dash when absent.
func intOrDash(n *int) string {
	if n == nil {
		return "—"
	}
	return fmt.Sprintf("%d", *n)
}
