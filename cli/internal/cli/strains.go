package cli

import (
	"context"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/prompt"
)

// strainFlagVars holds the flag targets shared by `strains create` and
// `strains edit`.
type strainFlagVars struct {
	name, breeder, lineage, strainType, status string
	source, notes, review, lastTried           string
	effects, flavors, terpenes, tags           []string
	rating                                     int
	thc, cbd                                   float64
}

// strainFormKeys are the fields `create` reads from flags and, when a terminal
// is answering, asks for. Every vocabulary field is here, so validateAnswers
// checks each one whichever door it came in through.
var strainFormKeys = []string{"name", "type", "status", "rating", "effect", "flavor", "terpene", "notes"}

func newStrainsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "strains",
		Short: "List, inspect, search, and manage marijuana strains",
		Long: "What you have tried, what you want to try, and what each one was like.\n" +
			"`list --status want_to_try` is the shopping list; `list --effect sleepy`\n" +
			"is how you pick one for tonight.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd,
		"Search strains by name, breeder, or lineage: icb strains search <query>",
		"See every value a strain field accepts: icb strains vocabulary",
	)
	cmd.AddCommand(
		newStrainsListCommand(),
		newStrainsShowCommand(),
		newStrainsSearchCommand(),
		newStrainsVocabularyCommand(),
		newStrainsCreateCommand(),
		newStrainsEditCommand(),
		newStrainsDeleteCommand(),
	)
	return cmd
}

func newStrainsListCommand() *cobra.Command {
	var (
		filter api.StrainFilter
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List strains by name",
		Long: "List the catalog by name. Every filter narrows together rather than\n" +
			"replacing the last one.\n" +
			"\n" +
			"--effect and --flavor each match one value inside a list, so a strain\n" +
			"carrying four effects is found by any of them.\n" +
			"\n" +
			"--limit caps what the filters left, so it takes the first names of the\n" +
			"narrowed set rather than filtering a capped slice.",
		Example: "  icb strains list                       the whole catalog\n" +
			"  icb strains list --status want_to_try  the shopping list\n" +
			"  icb strains list --effect sleepy       what to reach for tonight\n" +
			"  icb strains list --type sativa --rating-min 8\n" +
			"                                         the sativas worth repeating",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runStrainList(cmd, asJSON, func(c *api.Client) ([]api.Strain, error) {
				return c.ListStrains(cmd.Context(), filter, limitFlag(cmd))
			})
		},
	}
	cmd.Flags().StringVar(&filter.StrainType, "type", "", "Filter by classification (see: icb strains vocabulary)")
	cmd.Flags().StringVar(&filter.Status, "status", "", "Filter by status: tried, want_to_try")
	cmd.Flags().StringVar(&filter.Effect, "effect", "", "Filter to strains carrying this effect")
	cmd.Flags().StringVar(&filter.Flavor, "flavor", "", "Filter to strains carrying this flavor")
	cmd.Flags().IntVar(&filter.RatingMin, "rating-min", 0, "Only strains rated at least this (1-10)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output strains as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newStrainsSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "search <query>",
		Short: "Search strains by name, breeder, lineage, notes, or tags",
		Long: "Comma-separated terms preserve phrases (\"purple punch,grape\"); otherwise\n" +
			"whitespace splits into keywords matched against any field.",
		Example: "  icb strains search kush\n  icb strains search \"purple punch,grape\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runStrainList(cmd, asJSON, func(c *api.Client) ([]api.Strain, error) {
				return c.SearchStrains(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output strains as JSON to stdout")
	return cmd
}

func newStrainsVocabularyCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "vocabulary",
		Short: "Show every value a strain field accepts",
		Long: "The values --type, --status, --effect, --flavor and --terpene accept,\n" +
			"with how many strains carry each. A count of zero is a value nothing\n" +
			"uses yet, not a gap.\n" +
			"\n" +
			"Read from the server rather than compiled in, so a value added there\n" +
			"shows up here without upgrading this binary.",
		Example: "  icb strains vocabulary\n  icb strains vocabulary --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			vocabulary, err := client.GetStrainVocabulary(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), vocabulary)
			}
			printStrainVocabulary(cmd.OutOrStdout(), vocabulary)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the vocabulary as JSON to stdout")
	return cmd
}

func newStrainsShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <strain-id>",
		Short:   "Show a single strain",
		Example: "  icb strains show 12",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("strain id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			strain, err := client.GetStrain(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), strain)
			}
			printStrainDetail(cmd.OutOrStdout(), strain)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the strain as JSON to stdout")
	return cmd
}

// strainCreateFields is the record `strains create` builds, in the order it
// asks. The same list drives both doors: unanswered fields become the form, and
// the flags are checked against these validators before anything is sent.
//
// The choices are fetched rather than declared, because the vocabularies are
// lookup tables and adding a value to one is an INSERT on the server. A list
// compiled into this binary would make it a release instead. That is also why
// the client is built before the form rather than after it.
func strainCreateFields(ctx context.Context, client *api.Client) ([]prompt.Field, error) {
	vocabulary, err := client.GetStrainVocabulary(ctx)
	if err != nil {
		return nil, err
	}
	types := api.VocabularyNames(vocabulary.Types)
	statuses := api.VocabularyNames(vocabulary.Statuses)
	effects := api.VocabularyNames(vocabulary.Effects)
	flavors := api.VocabularyNames(vocabulary.Flavors)
	terpenes := api.VocabularyNames(vocabulary.Terpenes)

	return []prompt.Field{
		{Key: "name", Label: "Name"},
		{
			Key:      "type",
			Label:    "Type",
			Hint:     "Indica, sativa, or where between the two it sits.",
			Choices:  types,
			Optional: true,
			Validate: prompt.OneOf(types),
		},
		{
			Key:      "status",
			Label:    "Status",
			Hint:     "Whether you have had this one yet.",
			Default:  "want_to_try",
			Choices:  statuses,
			Validate: prompt.OneOf(statuses),
		},
		{
			Key:      "rating",
			Label:    "Rating",
			Hint:     "1 to 10, against how every other strain went — not against the rest of this list.",
			Optional: true,
			Validate: strainRating,
		},
		{
			Key:      "effect",
			Label:    "Effect",
			Hint:     "Asked again until you leave it empty.",
			Choices:  effects,
			Optional: true,
			Repeat:   true,
			Validate: prompt.OneOf(effects),
		},
		{
			Key:      "flavor",
			Label:    "Flavor",
			Choices:  flavors,
			Optional: true,
			Repeat:   true,
			Validate: prompt.OneOf(flavors),
		},
		{
			Key:      "terpene",
			Label:    "Terpene",
			Choices:  terpenes,
			Optional: true,
			Repeat:   true,
			Validate: prompt.OneOf(terpenes),
		},
		{Key: "notes", Label: "Notes", Optional: true, Multiline: true},
	}, nil
}

// strainRating accepts a whole number from 1 to 10, the range the check
// constraint on the column enforces. Refusing here says so before the round
// trip, and says it the same way through the flag and the prompt.
func strainRating(answer string) (string, error) {
	n, err := strconv.Atoi(answer)
	if err != nil {
		return "", fmt.Errorf("%q is not a whole number", answer)
	}
	if n < 1 || n > 10 {
		return "", fmt.Errorf("a rating runs 1 to 10, got %d", n)
	}
	return strconv.Itoa(n), nil
}

func newStrainsCreateCommand() *cobra.Command {
	var (
		v      strainFlagVars
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "create [flags]",
		Short: "Create a new strain",
		Long: "Only --name is required; a strain copied off a menu board has nothing\n" +
			"else yet. Run it from a terminal with no --name and it asks.",
		Example: "  icb strains create\n" +
			"  icb strains create --name \"Blue Dream\"\n" +
			"  icb strains create --name \"Zkittlez\" --type indica_dominant --status tried \\\n" +
			"      --rating 9 --effect happy --effect relaxed --flavor tropical",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			fields, err := strainCreateFields(cmd.Context(), client)
			if err != nil {
				return handleAPIError(err)
			}
			answers := flagAnswers(cmd, strainFormKeys...)
			if err := validateAnswers(answers, fields); err != nil {
				return usageError{err}
			}
			if missing := missingFlags(answers, "name"); len(missing) > 0 {
				if !interactive(cmd) {
					return usageError{fmt.Errorf("%s required — pass it, or run from a terminal to be asked", strings.Join(missing, " and "))}
				}
				asked, err := runForm(cmd, prompt.Form{
					Intro:  "Creating a strain. Ctrl-C to abandon it.",
					Fields: unanswered(fields, answers),
				})
				if errors.Is(err, errAborted) {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nAborted.")
					return nil
				}
				if err != nil {
					return err
				}
				answers.Merge(asked)
			}

			in := api.StrainCreateInput{Name: answers.Get("name")}
			if answers.Has("status") {
				in.Status = ptr(answers.Get("status"))
			}
			if answers.Has("type") {
				in.StrainType = ptr(answers.Get("type"))
			}
			if answers.Has("rating") {
				// Unfailable: pflag parses the flag as an int and strainRating
				// parses the typed answer, so nothing unparsed reaches here.
				rating, _ := strconv.Atoi(answers.Get("rating"))
				in.Rating = &rating
			}
			in.Effects = answers.All("effect")
			in.Flavors = answers.All("flavor")
			in.Terpenes = answers.All("terpene")
			if answers.Has("notes") {
				in.Notes = ptr(answers.Get("notes"))
			}

			f := cmd.Flags()
			in.Breeder = strFlag(f, "breeder", &v.breeder)
			in.Lineage = strFlag(f, "lineage", &v.lineage)
			in.THCPercent = floatFlag(f, "thc", &v.thc)
			in.CBDPercent = floatFlag(f, "cbd", &v.cbd)
			in.Source = strFlag(f, "source", &v.source)
			in.Review = strFlag(f, "review", &v.review)
			in.LastTriedDate = strFlag(f, "last-tried", &v.lastTried)
			if f.Changed("tag") {
				in.Tags = v.tags
			}

			strain, err := client.CreateStrain(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), strain)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created strain %q (id %d)\n", strain.Name, strain.ID)
			return nil
		},
	}
	addStrainFlags(cmd, &v)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created strain as JSON to stdout")
	return cmd
}

func newStrainsEditCommand() *cobra.Command {
	var (
		v      strainFlagVars
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "edit <strain-id> [flags]",
		Short: "Change fields on an existing strain",
		Long: "Update only the fields whose flags you pass.\n" +
			"\n" +
			"A repeatable flag replaces the whole list rather than adding to it, so\n" +
			"--effect sleepy leaves a strain with exactly one effect. Pass --clear-effects\n" +
			"to empty one.",
		Example: "  icb strains edit 12 --status tried --rating 8\n" +
			"  icb strains edit 12 --effect relaxed --effect sleepy\n" +
			"  icb strains edit 12 --clear-effects",
		Args: usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("strain id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			fields, err := strainCreateFields(cmd.Context(), client)
			if err != nil {
				return handleAPIError(err)
			}
			answers := flagAnswers(cmd, strainFormKeys...)
			if err := validateAnswers(answers, fields); err != nil {
				return usageError{err}
			}

			f := cmd.Flags()
			in := api.StrainUpdateInput{}
			in.Name = strFlag(f, "name", &v.name)
			in.Breeder = strFlag(f, "breeder", &v.breeder)
			in.Lineage = strFlag(f, "lineage", &v.lineage)
			in.Source = strFlag(f, "source", &v.source)
			in.Notes = strFlag(f, "notes", &v.notes)
			in.Review = strFlag(f, "review", &v.review)
			in.LastTriedDate = strFlag(f, "last-tried", &v.lastTried)
			in.THCPercent = floatFlag(f, "thc", &v.thc)
			in.CBDPercent = floatFlag(f, "cbd", &v.cbd)
			in.Rating = intFlag(f, "rating", &v.rating)
			if answers.Has("type") {
				in.StrainType = ptr(answers.Get("type"))
			}
			if answers.Has("status") {
				in.Status = ptr(answers.Get("status"))
			}
			in.Effects = listFlag(f, "effect", "clear-effects", answers.All("effect"))
			in.Flavors = listFlag(f, "flavor", "clear-flavors", answers.All("flavor"))
			in.Terpenes = listFlag(f, "terpene", "clear-terpenes", answers.All("terpene"))
			in.Tags = listFlag(f, "tag", "clear-tags", v.tags)

			if isEmptyStrainUpdate(in) {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag")}
			}

			strain, err := client.UpdateStrain(cmd.Context(), id, in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), strain)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated strain %q (id %d)\n", strain.Name, strain.ID)
			return nil
		},
	}
	addStrainFlags(cmd, &v)
	cmd.Flags().Bool("clear-effects", false, "Remove every effect from the strain")
	cmd.Flags().Bool("clear-flavors", false, "Remove every flavor from the strain")
	cmd.Flags().Bool("clear-terpenes", false, "Remove every terpene from the strain")
	cmd.Flags().Bool("clear-tags", false, "Remove every tag from the strain")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated strain as JSON to stdout")
	return cmd
}

func newStrainsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <strain-id>",
		Short:   "Delete a strain",
		Example: "  icb strains delete 12 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("strain id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			strain, err := client.GetStrain(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd, fmt.Sprintf("Delete strain %q (id %d)?", strain.Name, strain.ID))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteStrain(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted strain %q (id %d)\n", strain.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// addStrainFlags registers the shared create/edit flags on cmd.
//
// The vocabulary flags name no values in their help, because the values live in
// a lookup table this binary does not carry. `icb strains vocabulary` prints
// them, and a wrong one is refused with the list of what would have worked.
func addStrainFlags(cmd *cobra.Command, v *strainFlagVars) {
	f := cmd.Flags()
	f.StringVar(&v.name, "name", "", "Strain name (asked for when omitted)")
	f.StringVar(&v.breeder, "breeder", "", "Who bred it")
	f.StringVar(&v.lineage, "lineage", "", "Parent cross, e.g. \"Blueberry x Haze\"")
	f.StringVar(&v.strainType, "type", "", "Classification (see: icb strains vocabulary)")
	f.StringVar(&v.status, "status", "", "One of: tried, want_to_try")
	f.Float64Var(&v.thc, "thc", 0, "THC percentage")
	f.Float64Var(&v.cbd, "cbd", 0, "CBD percentage")
	f.IntVar(&v.rating, "rating", 0, "Rating from 1 to 10")
	f.StringArrayVar(&v.effects, "effect", nil, "Effect (repeatable; see: icb strains vocabulary)")
	f.StringArrayVar(&v.flavors, "flavor", nil, "Flavor (repeatable; see: icb strains vocabulary)")
	f.StringArrayVar(&v.terpenes, "terpene", nil, "Terpene (repeatable; see: icb strains vocabulary)")
	f.StringArrayVar(&v.tags, "tag", nil, "Tag (repeatable)")
	f.StringVar(&v.source, "source", "", "Dispensary or shop it came from")
	f.StringVar(&v.notes, "notes", "", "Notes")
	f.StringVar(&v.review, "review", "", "Review text")
	f.StringVar(&v.lastTried, "last-tried", "", "Date last tried, as YYYY-MM-DD")
}

// listFlag resolves one repeatable field on an update into the three states the
// wire has to tell apart: leave it alone, replace it, or empty it.
//
// nil is omitted from the body, so the column keeps what it holds. A pointer to
// an empty slice sends [] and clears it — which is why the clear is its own
// flag rather than an empty --effect, a spelling pflag cannot distinguish from
// the flag never appearing.
func listFlag(f *pflag.FlagSet, name, clearName string, values []string) *[]string {
	if cleared, err := f.GetBool(clearName); err == nil && cleared {
		empty := []string{}
		return &empty
	}
	if !f.Changed(name) {
		return nil
	}
	return &values
}

// isEmptyStrainUpdate reports whether no fields were set on a partial update.
// Written out rather than compared against a zero value, because the slice
// pointers make StrainUpdateInput comparable only by field.
func isEmptyStrainUpdate(in api.StrainUpdateInput) bool {
	return in.Name == nil && in.Breeder == nil && in.Lineage == nil && in.StrainType == nil &&
		in.Status == nil && in.THCPercent == nil && in.CBDPercent == nil && in.Rating == nil &&
		in.Effects == nil && in.Flavors == nil && in.Terpenes == nil && in.Tags == nil &&
		in.Source == nil && in.Notes == nil && in.Review == nil && in.LastTriedDate == nil
}

// ptr returns a pointer to v, for the optional fields the wire omits when nil.
func ptr[T any](v T) *T { return &v }

func runStrainList(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.Strain, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	strains, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), strains)
	}
	printStrainsTable(cmd.OutOrStdout(), strains)
	return nil
}

func printStrainsTable(out io.Writer, strains []api.Strain) {
	if len(strains) == 0 {
		_, _ = fmt.Fprintln(out, "No strains.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tSTATUS\tTYPE\tTHC\tCBD\tRATING\tNAME")
	for _, s := range strains {
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\t%s\t%s\t%s\t%s\n",
			s.ID, s.Status, strValue(s.StrainType), percentOrDash(s.THCPercent), percentOrDash(s.CBDPercent), intOrDash(s.Rating), s.Name)
	}
	_ = tw.Flush()
}

func printStrainDetail(out io.Writer, s api.Strain) {
	_, _ = fmt.Fprintf(out, "%s\n", s.Name)
	_, _ = fmt.Fprintf(out, "  id:        %d\n", s.ID)
	_, _ = fmt.Fprintf(out, "  status:    %s\n", s.Status)
	if v := strValue(s.StrainType); v != "" {
		_, _ = fmt.Fprintf(out, "  type:      %s\n", v)
	}
	if s.Rating != nil {
		_, _ = fmt.Fprintf(out, "  rating:    %d/10\n", *s.Rating)
	}
	if s.THCPercent != nil {
		_, _ = fmt.Fprintf(out, "  thc:       %s\n", percentOrDash(s.THCPercent))
	}
	if s.CBDPercent != nil {
		_, _ = fmt.Fprintf(out, "  cbd:       %s\n", percentOrDash(s.CBDPercent))
	}
	if v := strValue(s.Breeder); v != "" {
		_, _ = fmt.Fprintf(out, "  breeder:   %s\n", v)
	}
	if v := strValue(s.Lineage); v != "" {
		_, _ = fmt.Fprintf(out, "  lineage:   %s\n", v)
	}
	_, _ = fmt.Fprintf(out, "  effects:   %s\n", orNone(strings.Join(s.Effects, ", ")))
	_, _ = fmt.Fprintf(out, "  flavors:   %s\n", orNone(strings.Join(s.Flavors, ", ")))
	_, _ = fmt.Fprintf(out, "  terpenes:  %s\n", orNone(strings.Join(s.Terpenes, ", ")))
	if len(s.Tags) > 0 {
		_, _ = fmt.Fprintf(out, "  tags:      %s\n", strings.Join(s.Tags, ", "))
	}
	if v := strValue(s.Source); v != "" {
		_, _ = fmt.Fprintf(out, "  source:    %s\n", v)
	}
	if s.LastTriedDate != nil {
		_, _ = fmt.Fprintf(out, "  last tried: %s\n", *s.LastTriedDate)
	}
	if v := strValue(s.Notes); v != "" {
		_, _ = fmt.Fprintf(out, "  notes:     %s\n", v)
	}
	if v := strValue(s.Review); v != "" {
		_, _ = fmt.Fprintf(out, "  review:    %s\n", v)
	}
}

func printStrainVocabulary(out io.Writer, v api.StrainVocabulary) {
	sections := []struct {
		label   string
		entries []api.StrainVocabularyEntry
	}{
		{"type", v.Types},
		{"status", v.Statuses},
		{"effect", v.Effects},
		{"flavor", v.Flavors},
		{"terpene", v.Terpenes},
	}
	for i, section := range sections {
		if i > 0 {
			_, _ = fmt.Fprintln(out)
		}
		_, _ = fmt.Fprintf(out, "%s\n", strings.ToUpper(section.label))
		tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
		for _, entry := range section.entries {
			_, _ = fmt.Fprintf(tw, "  %s\t%d\n", entry.Name, entry.Count)
		}
		_ = tw.Flush()
	}
}

// percentOrDash renders a nullable percentage as an em dash when absent.
func percentOrDash(n *float64) string {
	if n == nil {
		return "—"
	}
	return strconv.FormatFloat(*n, 'f', -1, 64) + "%"
}
