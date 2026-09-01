package cli

import (
	"fmt"
	"io"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
)

func newCookingTechniquesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "cooking-techniques",
		Short: "List, inspect, search, and manage cooking techniques",
		Long: "The how-and-why writeups behind the recipes — searing, emulsifying, laminating\n" +
			"— kept separately from any one recipe that uses them.",
		RunE: requireSubcommand,
	}
	withNotFoundHints(cmd,
		"Search techniques by name, summary, body, or tags: icb cooking-techniques search <query>")
	cmd.AddCommand(
		newCookingTechniquesListCommand(),
		newCookingTechniquesShowCommand(),
		newCookingTechniquesSlugCommand(),
		newCookingTechniquesSearchCommand(),
		newCookingTechniquesCategoriesCommand(),
		newCookingTechniquesCreateCommand(),
		newCookingTechniquesEditCommand(),
		newCookingTechniquesDeleteCommand(),
	)
	return cmd
}

func newCookingTechniquesListCommand() *cobra.Command {
	var (
		category  string
		ratingMin int
		asJSON    bool
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List cooking techniques",
		Long: "List techniques ordered by name. Optionally filter by --category (one of the\n" +
			"9 fixed categories) and/or --rating-min (1-5).",
		Example: "  icb cooking-techniques list\n" +
			"  icb cooking-techniques list --category flavor_development --rating-min 4",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			f := cmd.Flags()
			return runTechniqueList(cmd, asJSON, func(c *api.Client) ([]api.CookingTechnique, error) {
				return c.ListCookingTechniques(cmd.Context(), strFlag(f, "category", &category), intFlag(f, "rating-min", &ratingMin))
			})
		},
	}
	cmd.Flags().StringVar(&category, "category", "", "Filter by category — icb cooking-techniques categories prints them")
	cmd.Flags().IntVar(&ratingMin, "rating-min", 0, "Minimum rating (1-5)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output techniques as JSON to stdout")
	return cmd
}

func newCookingTechniquesSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search techniques by name, summary, body, or tags",
		Long:    "Comma- or whitespace-separated terms are matched independently (OR).",
		Example: "  icb cooking-techniques search emulsion\n  icb cooking-techniques search \"beans,soak\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runTechniqueList(cmd, asJSON, func(c *api.Client) ([]api.CookingTechnique, error) {
				return c.SearchCookingTechniques(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output techniques as JSON to stdout")
	return cmd
}

func newCookingTechniquesShowCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "show <technique-id>",
		Short:   "Show a single technique by id",
		Example: "  icb cooking-techniques show 3",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("technique id", args[0])
			if err != nil {
				return err
			}
			return runTechniqueDetail(cmd, asJSON, func(c *api.Client) (api.CookingTechnique, error) {
				return c.GetCookingTechnique(cmd.Context(), id)
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the technique as JSON to stdout")
	return cmd
}

func newCookingTechniquesSlugCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "slug <slug>",
		Short:   "Show a single technique by slug",
		Example: "  icb cooking-techniques slug 24-hour-bean-soak",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runTechniqueDetail(cmd, asJSON, func(c *api.Client) (api.CookingTechnique, error) {
				return c.GetCookingTechniqueBySlug(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the technique as JSON to stdout")
	return cmd
}

func newCookingTechniquesCategoriesCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "categories",
		Short:   "List all technique categories with counts",
		Example: "  icb cooking-techniques categories",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			categories, err := client.ListCookingTechniqueCategories(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), categories)
			}
			tw := tabwriter.NewWriter(cmd.OutOrStdout(), 0, 4, 2, ' ', 0)
			_, _ = fmt.Fprintln(tw, "COUNT\tCATEGORY")
			for _, cat := range categories {
				_, _ = fmt.Fprintf(tw, "%d\t%s\n", cat.Count, cat.Name)
			}
			_ = tw.Flush()
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output categories as JSON to stdout")
	return cmd
}

func newCookingTechniquesCreateCommand() *cobra.Command {
	var (
		name           string
		category       string
		summary        string
		body           string
		whyItWorks     string
		commonPitfalls string
		sourceURL      string
		sourceName     string
		tags           []string
		rating         int
		asJSON         bool
	)
	cmd := &cobra.Command{
		Use:   "create --name <name> --category <category> --summary <summary> --body <body> [flags]",
		Short: "Create a cooking technique",
		Long:  "Create a technique. --name, --category, --summary, and --body are required.\n--body is markdown.",
		Example: "  icb cooking-techniques create --name \"Bloom Spices\" --category flavor_development \\\n" +
			"    --summary \"Toast ground spices in fat to unlock fat-soluble aroma.\" \\\n" +
			"    --body \"## Steps\\n1. Heat fat...\" --tag spices --rating 5",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			f := cmd.Flags()
			if name == "" || category == "" || summary == "" || body == "" {
				return usageError{fmt.Errorf("--name, --category, --summary, and --body are all required")}
			}
			in := api.CookingTechniqueCreateInput{Name: name, Category: category, Summary: summary, Body: body}
			in.WhyItWorks = strFlag(f, "why-it-works", &whyItWorks)
			in.CommonPitfalls = strFlag(f, "common-pitfalls", &commonPitfalls)
			in.SourceURL = strFlag(f, "source-url", &sourceURL)
			in.SourceName = strFlag(f, "source-name", &sourceName)
			if f.Changed("tag") {
				in.Tags = tags
			}
			in.Rating = intFlag(f, "rating", &rating)

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			technique, err := client.CreateCookingTechnique(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), technique)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created technique %q (id %d, slug %s)\n", technique.Name, technique.ID, technique.Slug)
			return nil
		},
	}
	addTechniqueContentFlags(cmd, &name, &category, &summary, &body, &whyItWorks, &commonPitfalls, &sourceURL, &sourceName, &tags, &rating)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created technique as JSON to stdout")
	return cmd
}

func newCookingTechniquesEditCommand() *cobra.Command {
	var (
		name           string
		category       string
		summary        string
		body           string
		whyItWorks     string
		commonPitfalls string
		sourceURL      string
		sourceName     string
		tags           []string
		rating         int
		clear          []string
		asJSON         bool
	)
	cmd := &cobra.Command{
		Use:   "edit <technique-id> [flags]",
		Short: "Change fields on an existing technique",
		Long: "Update only the fields whose flags you pass. --clear <field> empties a field\n" +
			"(repeatable) — use it for the rating, which an empty string cannot clear.\n" +
			"It takes the underscored field name, not the flag spelling.",
		Example: "  icb cooking-techniques edit 3 --rating 4 --tag legumes\n  icb cooking-techniques edit 3 --clear rating",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("technique id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.CookingTechniqueUpdateInput{}
			in.Name = strFlag(f, "name", &name)
			in.Category = strFlag(f, "category", &category)
			in.Summary = strFlag(f, "summary", &summary)
			in.Body = strFlag(f, "body", &body)
			in.WhyItWorks = strFlag(f, "why-it-works", &whyItWorks)
			in.CommonPitfalls = strFlag(f, "common-pitfalls", &commonPitfalls)
			in.SourceURL = strFlag(f, "source-url", &sourceURL)
			in.SourceName = strFlag(f, "source-name", &sourceName)
			if f.Changed("tag") {
				in.Tags = tags
			}
			in.Rating = intFlag(f, "rating", &rating)

			if isEmptyTechniqueUpdate(in) && len(clear) == 0 {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag or --clear")}
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			technique, err := client.UpdateCookingTechnique(cmd.Context(), id, in, clear)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), technique)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated technique %q (id %d)\n", technique.Name, technique.ID)
			return nil
		},
	}
	addTechniqueContentFlags(cmd, &name, &category, &summary, &body, &whyItWorks, &commonPitfalls, &sourceURL, &sourceName, &tags, &rating)
	cmd.Flags().StringArrayVar(&clear, "clear", nil, "Empty a field, e.g. --clear rating (repeatable; underscored field name)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated technique as JSON to stdout")
	return cmd
}

func newCookingTechniquesDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <technique-id>",
		Short:   "Delete a technique",
		Example: "  icb cooking-techniques delete 3 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("technique id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			technique, err := client.GetCookingTechnique(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd,
					fmt.Sprintf("Delete technique %q (id %d)?", technique.Name, technique.ID))
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteCookingTechnique(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted technique %q (id %d)\n", technique.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

// addTechniqueContentFlags registers the shared create/edit content flags so the
// two commands stay in lockstep.
func addTechniqueContentFlags(cmd *cobra.Command, name, category, summary, body, whyItWorks, commonPitfalls, sourceURL, sourceName *string, tags *[]string, rating *int) {
	cmd.Flags().StringVar(name, "name", "", "Technique name")
	cmd.Flags().StringVar(category, "category", "", "Category — icb cooking-techniques categories prints them")
	cmd.Flags().StringVar(summary, "summary", "", "One-paragraph summary")
	cmd.Flags().StringVar(body, "body", "", "Full markdown body")
	cmd.Flags().StringVar(whyItWorks, "why-it-works", "", "Why-it-works explanation")
	cmd.Flags().StringVar(commonPitfalls, "common-pitfalls", "", "Common pitfalls")
	cmd.Flags().StringVar(sourceURL, "source-url", "", "Source URL")
	cmd.Flags().StringVar(sourceName, "source-name", "", "Source name")
	cmd.Flags().StringArrayVar(tags, "tag", nil, "Tag (repeatable; replaces the tag list)")
	cmd.Flags().IntVar(rating, "rating", 0, "Rating (1-5)")
}

func isEmptyTechniqueUpdate(in api.CookingTechniqueUpdateInput) bool {
	return in.Name == nil && in.Category == nil && in.Summary == nil && in.Body == nil &&
		in.WhyItWorks == nil && in.CommonPitfalls == nil && in.SourceURL == nil &&
		in.SourceName == nil && in.Tags == nil && in.Rating == nil
}

func runTechniqueList(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.CookingTechnique, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	techniques, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), techniques)
	}
	printTechniquesTable(cmd.OutOrStdout(), techniques)
	return nil
}

func runTechniqueDetail(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) (api.CookingTechnique, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	technique, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), technique)
	}
	printTechniqueDetail(cmd.OutOrStdout(), technique)
	return nil
}

func printTechniquesTable(out io.Writer, techniques []api.CookingTechnique) {
	if len(techniques) == 0 {
		_, _ = fmt.Fprintln(out, "No techniques.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "ID\tRATING\tCATEGORY\tNAME\tSLUG")
	for _, t := range techniques {
		_, _ = fmt.Fprintf(tw, "%d\t%s\t%s\t%s\t%s\n", t.ID, ratingStars(t.Rating), t.Category, t.Name, t.Slug)
	}
	_ = tw.Flush()
}

func printTechniqueDetail(out io.Writer, t api.CookingTechnique) {
	_, _ = fmt.Fprintf(out, "%s\n", t.Name)
	_, _ = fmt.Fprintf(out, "  id:        %d\n", t.ID)
	_, _ = fmt.Fprintf(out, "  slug:      %s\n", t.Slug)
	_, _ = fmt.Fprintf(out, "  category:  %s\n", t.Category)
	_, _ = fmt.Fprintf(out, "  rating:    %s\n", ratingStars(t.Rating))
	_, _ = fmt.Fprintf(out, "  tags:      %s\n", orNone(strings.Join(t.Tags, ", ")))
	if s := strValue(t.SourceName); s != "" {
		_, _ = fmt.Fprintf(out, "  source:    %s\n", s)
	}
	if s := strValue(t.SourceURL); s != "" {
		_, _ = fmt.Fprintf(out, "  url:       %s\n", s)
	}
	_, _ = fmt.Fprintf(out, "  summary:   %s\n", t.Summary)
	if s := strValue(t.WhyItWorks); s != "" {
		_, _ = fmt.Fprintf(out, "  why:       %s\n", s)
	}
	if s := strValue(t.CommonPitfalls); s != "" {
		_, _ = fmt.Fprintf(out, "  pitfalls:  %s\n", s)
	}
	_, _ = fmt.Fprintf(out, "\n%s\n", t.Body)
}

// ratingStars renders a nullable 1-5 rating; nil is a dash.
func ratingStars(rating *int) string {
	if rating == nil {
		return "-"
	}
	return strings.Repeat("*", *rating)
}
