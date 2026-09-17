package cli

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/prompt"
)

// errRatingRange is the refusal a rating outside 1..10 carries, so a test
// asserts the reason rather than the sentence spelling it.
var errRatingRange = errors.New("a rating runs 1 to 10")

// strainFlagVars holds the flag targets shared by `strains create` and
// `strains edit`.
type strainFlagVars struct {
	name, breeder, lineage, strainType, status string
	source, notes, review, lastTried           string
	effects, flavors, terpenes, tags           []string
	clear                                      []string
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
		Short: "List, inspect, search, and manage a catalog of strains",
		Long: "A catalog of cannabis strains: which have been tried, which are queued, and\n" +
			"what each one is like. `list --status want_to_try` is the queue;\n" +
			"`list --effect sleepy` narrows to a recorded effect.",
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
			"--effect, --flavor and --terpene each match one value inside a list, so a\n" +
			"strain carrying four effects is found by any of them.\n" +
			"\n" +
			"A filter value no lookup table carries is a usage error naming the values\n" +
			"that would have worked, rather than an empty list that reads as an empty\n" +
			"catalog.\n" +
			"\n" +
			"--limit caps what the filters left, so it takes the first names of the\n" +
			"narrowed set rather than filtering a capped slice.",
		Example: "  icb strains list                       the whole catalog\n" +
			"  icb strains list --status want_to_try  the queue\n" +
			"  icb strains list --effect sleepy       narrowed to a recorded effect\n" +
			"  icb strains list --type sativa --rating-min 8\n" +
			"                                         the highest-rated sativas",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			// A filter has no field to empty, so an empty value here is refused
			// rather than read as the clear it means on `edit`. It narrows
			// nothing, and it is almost always an unset shell variable.
			for _, name := range []string{"type", "status", "effect", "flavor", "terpene"} {
				if readFlagIntent(cmd.Flags(), name) == flagClears {
					return usageError{fmt.Errorf("--%s given an empty value — a filter needs something to match", name)}
				}
			}
			if cmd.Flags().Changed("rating-min") && (filter.RatingMin < 1 || filter.RatingMin > 10) {
				return usageError{fmt.Errorf("--rating-min: %w, got %d", errRatingRange, filter.RatingMin)}
			}
			return runStrainList(cmd, asJSON, filter, func(c *api.Client) ([]api.Strain, error) {
				return c.ListStrains(cmd.Context(), filter, limitFlag(cmd))
			})
		},
	}
	cmd.Flags().StringVar(&filter.StrainType, "type", "", "Filter by classification (see: icb strains vocabulary)")
	cmd.Flags().StringVar(&filter.Status, "status", "", "Filter by status: tried, want_to_try")
	cmd.Flags().StringVar(&filter.Effect, "effect", "", "Filter to strains carrying this effect")
	cmd.Flags().StringVar(&filter.Flavor, "flavor", "", "Filter to strains carrying this flavor")
	cmd.Flags().StringVar(&filter.Terpene, "terpene", "", "Filter to strains carrying this terpene")
	cmd.Flags().IntVar(&filter.RatingMin, "rating-min", 0, "Only strains rated at least this (1-10)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output strains as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newStrainsSearchCommand() *cobra.Command {
	var (
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "search <query>",
		Short: "Search strains by name, breeder, lineage, notes, or tags",
		Long: "Comma-separated terms preserve phrases (\"purple punch,grape\"); otherwise\n" +
			"whitespace splits into keywords matched against any field.",
		Example: "  icb strains search kush\n  icb strains search \"purple punch,grape\" --limit 5",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			filter := api.StrainFilter{Query: args[0]}
			return runStrainList(cmd, asJSON, filter, func(c *api.Client) ([]api.Strain, error) {
				return c.SearchStrains(cmd.Context(), args[0], limitFlag(cmd))
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output strains as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newStrainsVocabularyCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "vocabulary",
		Short: "Show every value a strain field accepts",
		Long: "The values --type, --status, --effect, --flavor and --terpene accept, with\n" +
			"how many strains carry each. A count of zero is a value nothing uses yet,\n" +
			"not a gap.",
		Example: "  icb strains vocabulary\n  icb strains vocabulary --json",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleStrainAPIError(err)
			}
			vocabulary, err := client.GetStrainVocabulary(cmd.Context())
			if err != nil {
				return handleStrainAPIError(err)
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
				return handleStrainAPIError(err)
			}
			strain, err := client.GetStrain(cmd.Context(), id)
			if err != nil {
				return handleStrainAPIError(err)
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
// The choices are fetched, which is why the client is built before the form —
// see `ichrisbirch/models/strain.py` for what that buys and what it costs.
func strainCreateFields(ctx context.Context, client *api.Client) ([]prompt.Field, error) {
	vocabulary, err := client.GetStrainVocabulary(ctx)
	if err != nil {
		return nil, err
	}
	types := api.VocabularyNames(vocabulary.StrainType)
	statuses := api.VocabularyNames(vocabulary.Status)
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
			Hint:     "Whether this one has been tried yet.",
			Default:  "want_to_try",
			Choices:  statuses,
			Validate: prompt.OneOf(statuses),
		},
		{
			Key:      "rating",
			Label:    "Rating",
			Hint:     "1 to 10, against an absolute scale rather than against the rest of this list.",
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
// constraint on the column enforces.
func strainRating(answer string) (string, error) {
	n, err := strconv.Atoi(answer)
	if err != nil {
		return "", fmt.Errorf("%q is not a whole number", answer)
	}
	if n < 1 || n > 10 {
		return "", fmt.Errorf("%w, got %d", errRatingRange, n)
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
			f := cmd.Flags()
			// Every refusal that needs no server state is decided here, before
			// the client exists. Deciding them after it would turn each one
			// into exit 1 whenever the API is unreachable, and a caller that
			// retries on 1 and fixes its arguments on 2 retries a typo forever.
			if readFlagIntent(f, "name") == flagClears {
				return usageError{fmt.Errorf("--name cannot be empty — every strain carries one")}
			}
			if f.Changed("rating") {
				if _, err := strainRating(strconv.Itoa(v.rating)); err != nil {
					return usageError{fmt.Errorf("--rating: %w", err)}
				}
			}
			if !f.Changed("name") && !interactive(cmd) {
				return usageError{fmt.Errorf("--name required — pass it, or run from a terminal to be asked")}
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleStrainAPIError(err)
			}
			fields, err := strainCreateFields(cmd.Context(), client)
			if err != nil {
				return handleStrainAPIError(err)
			}
			answers := flagAnswers(cmd, strainFormKeys...)
			if err := validateAnswers(answers, fields); err != nil {
				return usageError{err}
			}
			if !answers.Has("name") {
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

			in.Breeder = strainStrFlag(f, "breeder", &v.breeder)
			in.Lineage = strainStrFlag(f, "lineage", &v.lineage)
			in.THCPercent = floatFlag(f, "thc", &v.thc)
			in.CBDPercent = floatFlag(f, "cbd", &v.cbd)
			in.Source = strainStrFlag(f, "source", &v.source)
			in.Review = strainStrFlag(f, "review", &v.review)
			in.LastTriedDate = strainStrFlag(f, "last-tried", &v.lastTried)
			in.Tags = listFlag(f, "tag", v.tags)

			strain, err := client.CreateStrain(cmd.Context(), in)
			if err != nil {
				return handleStrainAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), strain)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created strain %q (id %d)\n", strain.Name, strain.ID)
			return nil
		},
	}
	addStrainFlags(cmd, &v)
	cmd.Flags().Lookup("name").Usage = "Strain name (asked for when omitted)"
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
			"--effect sleepy leaves a strain with exactly one effect.\n" +
			"\n" +
			"An empty value empties the field: --breeder \"\" removes the breeder and\n" +
			"--effect \"\" removes every effect. --name and --status cannot be emptied,\n" +
			"and say so.\n" +
			"\n" +
			"--clear <field> reaches the numeric fields, which cannot take an empty\n" +
			"value at all because the flag refuses to parse one.",
		Example: "  icb strains edit 12 --status tried --rating 8\n" +
			"  icb strains edit 12 --effect relaxed --effect sleepy\n" +
			"  icb strains edit 12 --breeder \"\" --effect \"\"\n" +
			"  icb strains edit 12 --clear rating --clear thc_percent",
		Args: usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("strain id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			// Every refusal that needs no server state is settled here, before
			// the client exists. Deciding them after it would turn each one
			// into exit 1 whenever the API is unreachable, and exit 2 is the
			// only signal that says retry with different arguments.
			if f.Changed("rating") {
				if _, err := strainRating(strconv.Itoa(v.rating)); err != nil {
					return usageError{fmt.Errorf("--rating: %w", err)}
				}
			}
			clear, err := strainClears(f, v.clear)
			if err != nil {
				return usageError{err}
			}

			in := api.StrainUpdateInput{}
			in.Name = strainStrFlag(f, "name", &v.name)
			in.Breeder = strainStrFlag(f, "breeder", &v.breeder)
			in.Lineage = strainStrFlag(f, "lineage", &v.lineage)
			in.StrainType = strainStrFlag(f, "type", &v.strainType)
			in.Status = strainStrFlag(f, "status", &v.status)
			in.Source = strainStrFlag(f, "source", &v.source)
			in.Notes = strainStrFlag(f, "notes", &v.notes)
			in.Review = strainStrFlag(f, "review", &v.review)
			in.LastTriedDate = strainStrFlag(f, "last-tried", &v.lastTried)
			in.THCPercent = floatFlag(f, "thc", &v.thc)
			in.CBDPercent = floatFlag(f, "cbd", &v.cbd)
			in.Rating = intFlag(f, "rating", &v.rating)
			in.Effects = listFlag(f, "effect", v.effects)
			in.Flavors = listFlag(f, "flavor", v.flavors)
			in.Terpenes = listFlag(f, "terpene", v.terpenes)
			in.Tags = listFlag(f, "tag", v.tags)

			if isEmptyStrainUpdate(in) && len(clear) == 0 {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag or --clear")}
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleStrainAPIError(err)
			}
			strain, err := client.UpdateStrain(cmd.Context(), id, in, clear)
			if err != nil {
				return handleStrainAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), strain)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated strain %q (id %d)\n", strain.Name, strain.ID)
			return nil
		},
	}
	addStrainFlags(cmd, &v)
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
				return handleStrainAPIError(err)
			}
			strain, err := client.GetStrain(cmd.Context(), id)
			if err != nil {
				return handleStrainAPIError(err)
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
				return handleStrainAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted strain %q (id %d)\n", strain.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// addStrainFlags registers the shared create/edit flags on cmd.
func addStrainFlags(cmd *cobra.Command, v *strainFlagVars) {
	f := cmd.Flags()
	f.StringVar(&v.name, "name", "", "Strain name")
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
	f.StringArrayVar(&v.clear, "clear", nil, "Empty a field, e.g. --clear rating (repeatable; underscored field name)")
}

// rawFlagValues reads every value a flag holds, empties included — which is the
// difference from flagValues, whose job is to drop them.
func rawFlagValues(flag *pflag.Flag) []string {
	if slice, ok := flag.Value.(pflag.SliceValue); ok {
		return slice.GetSlice()
	}
	return []string{flag.Value.String()}
}

// flagIntent is what one field flag on this run is asking for.
type flagIntent int

const (
	flagUntouched flagIntent = iota
	flagCarriesValues
	flagClears
	flagMixesEmptyWithValues
)

// readFlagIntent classifies a field flag by the values it holds.
//
// `""` clears the field, on every field flag that can carry one. A caller
// learns what an empty value does from whichever flag they reach for first and
// uses the next the same way, so one verb cannot answer several ways without
// the disagreement being invisible — nothing on screen shows which reading a
// flag took.
func readFlagIntent(f *pflag.FlagSet, name string) flagIntent {
	flag := f.Lookup(name)
	if flag == nil || !flag.Changed {
		return flagUntouched
	}
	var empty, filled int
	for _, value := range rawFlagValues(flag) {
		if strings.TrimSpace(value) == "" {
			empty++
		} else {
			filled++
		}
	}
	switch {
	case empty > 0 && filled > 0:
		return flagMixesEmptyWithValues
	case empty > 0:
		return flagClears
	default:
		return flagCarriesValues
	}
}

// strainClearableFlags maps each field flag to the record field an empty value
// empties. `name` and `status` are absent: their columns are NOT NULL, so there
// is nothing to empty them to.
//
// The numeric flags are absent for a different reason — pflag refuses to parse
// `""` as an int or a float, so the flag never reaches a handler. `--clear
// <field>` is what reaches those, and is the same grammar `icb recipes edit`
// and `icb cooking-techniques edit` already take.
var strainClearableFlags = map[string]string{
	"breeder": "breeder", "lineage": "lineage", "type": "strain_type",
	"effect": "effects", "flavor": "flavors", "terpene": "terpenes",
	"tag": "tags", "source": "source", "notes": "notes",
	"review": "review", "last-tried": "last_tried_date",
}

// strainRequiredFlags are the two whose column cannot hold a null.
var strainRequiredFlags = []string{"name", "status"}

// strainClearFields maps a --clear argument to the flag setting the same field,
// so asking for both can be refused rather than silently resolved either way.
var strainClearFields = map[string]string{
	"breeder": "breeder", "lineage": "lineage", "strain_type": "type",
	"thc_percent": "thc", "cbd_percent": "cbd", "rating": "rating",
	"effects": "effect", "flavors": "flavor", "terpenes": "terpene",
	"tags": "tag", "source": "source", "notes": "notes",
	"review": "review", "last_tried_date": "last-tried",
}

// strainClears resolves everything this run empties: the fields --clear names,
// and the fields whose flag was passed an empty value.
func strainClears(f *pflag.FlagSet, explicit []string) ([]string, error) {
	for _, name := range strainRequiredFlags {
		if readFlagIntent(f, name) == flagClears {
			return nil, fmt.Errorf("--%s cannot be emptied — every strain carries one", name)
		}
	}

	clearing := map[string]bool{}
	for _, field := range explicit {
		flagName, known := strainClearFields[field]
		if !known {
			return nil, fmt.Errorf("--clear %s is not a clearable strain field — use the underscored name, such as --clear strain_type", field)
		}
		if readFlagIntent(f, flagName) == flagCarriesValues {
			return nil, fmt.Errorf("--clear %s and --%s both given — pass one", field, flagName)
		}
		clearing[field] = true
	}

	for flagName, field := range strainClearableFlags {
		switch readFlagIntent(f, flagName) {
		case flagClears:
			clearing[field] = true
		case flagMixesEmptyWithValues:
			return nil, fmt.Errorf("--%s given both a value and an empty one — an empty value empties the field, so pass one or the other", flagName)
		case flagUntouched, flagCarriesValues:
		}
	}

	fields := make([]string, 0, len(clearing))
	for field := range clearing {
		fields = append(fields, field)
	}
	sort.Strings(fields)
	return fields, nil
}

// listFlag returns the values a repeatable flag holds, or nil when it was never
// passed or is emptying the field — in which case the clear list carries it.
func listFlag(f *pflag.FlagSet, name string, values []string) []string {
	if readFlagIntent(f, name) != flagCarriesValues {
		return nil
	}
	return values
}

// strFlag clearing a field is carried by the clear list, not by an empty value
// in the body, so a clearing flag reads as untouched here.
func strainStrFlag(f *pflag.FlagSet, name string, v *string) *string {
	if readFlagIntent(f, name) != flagCarriesValues {
		return nil
	}
	return v
}

// isEmptyStrainUpdate reports whether no field flag was set.
//
// Written out rather than compared against the zero value, because the four
// `[]string` fields make the struct non-comparable and `in == zero` does not
// compile. `api.EventUpdateInput` has no slice and does use the comparison.
func isEmptyStrainUpdate(in api.StrainUpdateInput) bool {
	return in.Name == nil && in.Breeder == nil && in.Lineage == nil && in.StrainType == nil &&
		in.Status == nil && in.THCPercent == nil && in.CBDPercent == nil && in.Rating == nil &&
		in.Effects == nil && in.Flavors == nil && in.Terpenes == nil && in.Tags == nil &&
		in.Source == nil && in.Notes == nil && in.Review == nil && in.LastTriedDate == nil
}

// handleStrainAPIError maps a 422 to a usage error.
//
// The API refuses an unknown vocabulary value with a 422 naming the values that
// would have worked, which is a usage mistake wherever it arrives. Left as a
// generic failure it exits 1, and a caller that retries on 1 and fixes its
// arguments on 2 retries a typo forever.
func handleStrainAPIError(err error) error {
	var apiErr *api.APIError
	if errors.As(err, &apiErr) && apiErr.StatusCode == http.StatusUnprocessableEntity && apiErr.Message != "" {
		return usageError{errors.New(apiErr.Message)}
	}
	return handleAPIError(err)
}

// ptr returns a pointer to v, for the optional fields the wire omits when nil.
func ptr[T any](v T) *T { return &v }

func runStrainList(cmd *cobra.Command, asJSON bool, filter api.StrainFilter, fetch func(*api.Client) ([]api.Strain, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleStrainAPIError(err)
	}
	strains, err := fetch(client)
	if err != nil {
		return handleStrainAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), strains)
	}
	printStrainsTable(cmd.OutOrStdout(), strains, filter)
	return nil
}

func printStrainsTable(out io.Writer, strains []api.Strain, filter api.StrainFilter) {
	if len(strains) == 0 {
		// A count is measured under whatever narrowed it, so the empty state
		// names the narrowing rather than reading as an empty catalog.
		if active := filter.Active(); len(active) > 0 {
			_, _ = fmt.Fprintf(out, "No strains match %s.\n", strings.Join(active, " "))
			return
		}
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
	_, _ = fmt.Fprintf(out, "  id:         %d\n", s.ID)
	_, _ = fmt.Fprintf(out, "  status:     %s\n", s.Status)
	if v := strValue(s.StrainType); v != "" {
		_, _ = fmt.Fprintf(out, "  type:       %s\n", v)
	}
	if s.Rating != nil {
		_, _ = fmt.Fprintf(out, "  rating:     %d/10\n", *s.Rating)
	}
	if s.THCPercent != nil {
		_, _ = fmt.Fprintf(out, "  thc:        %s\n", percentOrDash(s.THCPercent))
	}
	if s.CBDPercent != nil {
		_, _ = fmt.Fprintf(out, "  cbd:        %s\n", percentOrDash(s.CBDPercent))
	}
	if v := strValue(s.Breeder); v != "" {
		_, _ = fmt.Fprintf(out, "  breeder:    %s\n", v)
	}
	if v := strValue(s.Lineage); v != "" {
		_, _ = fmt.Fprintf(out, "  lineage:    %s\n", v)
	}
	_, _ = fmt.Fprintf(out, "  effects:    %s\n", orNone(strings.Join(s.Effects, ", ")))
	_, _ = fmt.Fprintf(out, "  flavors:    %s\n", orNone(strings.Join(s.Flavors, ", ")))
	_, _ = fmt.Fprintf(out, "  terpenes:   %s\n", orNone(strings.Join(s.Terpenes, ", ")))
	if len(s.Tags) > 0 {
		_, _ = fmt.Fprintf(out, "  tags:       %s\n", strings.Join(s.Tags, ", "))
	}
	if v := strValue(s.Source); v != "" {
		_, _ = fmt.Fprintf(out, "  source:     %s\n", v)
	}
	if s.LastTriedDate != nil {
		_, _ = fmt.Fprintf(out, "  last tried: %s\n", *s.LastTriedDate)
	}
	if v := strValue(s.Notes); v != "" {
		_, _ = fmt.Fprintf(out, "  notes:      %s\n", v)
	}
	if v := strValue(s.Review); v != "" {
		_, _ = fmt.Fprintf(out, "  review:     %s\n", v)
	}
}

func printStrainVocabulary(out io.Writer, v api.StrainVocabulary) {
	sections := []struct {
		label   string
		entries []api.StrainVocabularyEntry
	}{
		{"strain_type", v.StrainType},
		{"status", v.Status},
		{"effects", v.Effects},
		{"flavors", v.Flavors},
		{"terpenes", v.Terpenes},
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
