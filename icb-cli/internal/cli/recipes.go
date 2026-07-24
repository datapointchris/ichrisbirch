package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"ichrisbirch/cli/internal/api"
)

func newRecipesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "recipes",
		Short: "List, inspect, search, cook, and AI-import recipes",
		Long: "Work with the recipe catalog in the ichrisbirch API as yourself, including\n" +
			"the AI suggest/import flows. Requires a logged-in session (`icb auth login`).",
		RunE: requireSubcommand,
	}
	cmd.AddCommand(
		newRecipesListCommand(),
		newRecipesViewCommand(),
		newRecipesSearchCommand(),
		newRecipesSearchIngredientsCommand(),
		newRecipesCreateCommand(),
		newRecipesEditCommand(),
		newRecipesDeleteCommand(),
		newRecipesMadeCommand(),
		newRecipesAISuggestCommand(),
		newRecipesAISaveCommand(),
		newRecipesAIImportCommand(),
		newRecipesAISaveImportCommand(),
	)
	return cmd
}

func newRecipesListCommand() *cobra.Command {
	var (
		cuisine      string
		mealType     string
		difficulty   string
		ratingMin    int
		maxTotalTime int
		asJSON       bool
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List recipes",
		Long:  "List recipes ordered by name, optionally filtered.",
		Example: "  icb recipes list\n" +
			"  icb recipes list --cuisine italian --rating-min 4 --max-total-time 45",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			f := cmd.Flags()
			return runRecipeList(cmd, asJSON, func(c *api.Client) ([]api.Recipe, error) {
				return c.ListRecipes(cmd.Context(),
					strFlag(f, "cuisine", &cuisine), strFlag(f, "meal-type", &mealType), strFlag(f, "difficulty", &difficulty),
					intFlag(f, "rating-min", &ratingMin), intFlag(f, "max-total-time", &maxTotalTime))
			})
		},
	}
	cmd.Flags().StringVar(&cuisine, "cuisine", "", "Filter by cuisine")
	cmd.Flags().StringVar(&mealType, "meal-type", "", "Filter by meal type")
	cmd.Flags().StringVar(&difficulty, "difficulty", "", "Filter by difficulty")
	cmd.Flags().IntVar(&ratingMin, "rating-min", 0, "Minimum rating (1-5)")
	cmd.Flags().IntVar(&maxTotalTime, "max-total-time", 0, "Maximum total time in minutes")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output recipes as JSON to stdout")
	return cmd
}

func newRecipesViewCommand() *cobra.Command {
	var (
		servings int
		asJSON   bool
	)
	cmd := &cobra.Command{
		Use:     "view <recipe-id>",
		Short:   "Show a single recipe with ingredients",
		Long:    "Pass --servings to scale each ingredient (scaled_quantity in the output).",
		Example: "  icb recipes view 2\n  icb recipes view 2 --servings 12",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("recipe id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			recipe, err := client.GetRecipe(cmd.Context(), id, intFlag(cmd.Flags(), "servings", &servings))
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), recipe)
			}
			printRecipeDetail(cmd.OutOrStdout(), recipe)
			return nil
		},
	}
	cmd.Flags().IntVar(&servings, "servings", 0, "Scale ingredient quantities to this serving count")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the recipe as JSON to stdout")
	return cmd
}

func newRecipesSearchCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "search <query>",
		Short:   "Search recipes by name, instructions, or tags",
		Long:    "Comma- or whitespace-separated terms are matched independently (OR).",
		Example: "  icb recipes search oatmeal\n  icb recipes search \"chicken,lemon\"",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runRecipeList(cmd, asJSON, func(c *api.Client) ([]api.Recipe, error) {
				return c.SearchRecipes(cmd.Context(), args[0])
			})
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output recipes as JSON to stdout")
	return cmd
}

func newRecipesSearchIngredientsCommand() *cobra.Command {
	var (
		match  string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "search-ingredients <ingredients>",
		Short: "Find recipes by ingredients you have",
		Long: "Rank recipes by how many of the comma-separated ingredients they contain.\n" +
			"--match any (default) ranks by coverage; --match all requires every ingredient.",
		Example: "  icb recipes search-ingredients \"chicken,lemon,garlic\"\n" +
			"  icb recipes search-ingredients \"oats,milk\" --match all",
		Args: usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if match != "any" && match != "all" {
				return usageError{fmt.Errorf("--match must be 'any' or 'all'")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			results, err := client.SearchRecipesByIngredients(cmd.Context(), args[0], match)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), results)
			}
			printIngredientSearchTable(cmd.OutOrStdout(), results)
			return nil
		},
	}
	cmd.Flags().StringVar(&match, "match", "any", "Match mode: any (rank by coverage) or all (require every ingredient)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output results as JSON to stdout")
	return cmd
}

func newRecipesCreateCommand() *cobra.Command {
	var (
		name            string
		instructions    string
		ingredientsJSON string
		description     string
		sourceURL       string
		sourceName      string
		prepTime        int
		cookTime        int
		totalTime       int
		servings        int
		difficulty      string
		cuisine         string
		mealType        string
		tags            []string
		notes           string
		rating          int
		asJSON          bool
	)
	cmd := &cobra.Command{
		Use:   "create --name <name> --instructions <text> [flags]",
		Short: "Create a recipe",
		Long: "Create a recipe. --name and --instructions are required. --ingredients-json\n" +
			"is a JSON array of {quantity,unit,item,prep_note,is_optional,ingredient_group}.",
		Example: "  icb recipes create --name \"Chimichurri\" --instructions \"Blend all.\" \\\n" +
			"    --ingredients-json '[{\"quantity\":1,\"unit\":\"cup\",\"item\":\"parsley\"}]' --cuisine argentine",
		Args: usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			f := cmd.Flags()
			if name == "" || instructions == "" {
				return usageError{fmt.Errorf("--name and --instructions are required")}
			}
			ingredients, err := parseIngredientsJSON(ingredientsJSON)
			if err != nil {
				return err
			}
			in := api.RecipeCreateInput{
				Name:         name,
				Instructions: instructions,
				Ingredients:  ingredients,
				Servings:     servings,
			}
			in.Description = strFlag(f, "description", &description)
			in.SourceURL = strFlag(f, "source-url", &sourceURL)
			in.SourceName = strFlag(f, "source-name", &sourceName)
			in.PrepTimeMinutes = intFlag(f, "prep-time", &prepTime)
			in.CookTimeMinutes = intFlag(f, "cook-time", &cookTime)
			in.TotalTimeMinutes = intFlag(f, "total-time", &totalTime)
			in.Difficulty = strFlag(f, "difficulty", &difficulty)
			in.Cuisine = strFlag(f, "cuisine", &cuisine)
			in.MealType = strFlag(f, "meal-type", &mealType)
			if f.Changed("tag") {
				in.Tags = tags
			}
			in.Notes = strFlag(f, "notes", &notes)
			in.Rating = intFlag(f, "rating", &rating)

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			recipe, err := client.CreateRecipe(cmd.Context(), in)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), recipe)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Created recipe %q (id %d)\n", recipe.Name, recipe.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Recipe name")
	cmd.Flags().StringVar(&instructions, "instructions", "", "Instructions (markdown)")
	cmd.Flags().StringVar(&ingredientsJSON, "ingredients-json", "", "JSON array of ingredient objects")
	cmd.Flags().IntVar(&servings, "servings", 4, "Number of servings")
	addRecipeScalarFlags(cmd, &description, &sourceURL, &sourceName, &prepTime, &cookTime, &totalTime, &difficulty, &cuisine, &mealType, &tags, &notes, &rating)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the created recipe as JSON to stdout")
	return cmd
}

func newRecipesEditCommand() *cobra.Command {
	var (
		name            string
		instructions    string
		ingredientsJSON string
		description     string
		sourceURL       string
		sourceName      string
		prepTime        int
		cookTime        int
		totalTime       int
		servings        int
		difficulty      string
		cuisine         string
		mealType        string
		tags            []string
		notes           string
		rating          int
		clear           []string
		asJSON          bool
	)
	cmd := &cobra.Command{
		Use:   "edit <recipe-id> [flags]",
		Short: "Change fields on an existing recipe",
		Long: "Update only the fields whose flags you pass. --ingredients-json replaces the\n" +
			"whole ingredient list. --clear <field> sets a field to null (repeatable) —\n" +
			"use it for numeric fields an empty string cannot clear.",
		Example: "  icb recipes edit 2 --rating 5\n  icb recipes edit 2 --clear cuisine --clear rating",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("recipe id", args[0])
			if err != nil {
				return err
			}
			f := cmd.Flags()
			in := api.RecipeUpdateInput{}
			in.Name = strFlag(f, "name", &name)
			in.Instructions = strFlag(f, "instructions", &instructions)
			in.Description = strFlag(f, "description", &description)
			in.SourceURL = strFlag(f, "source-url", &sourceURL)
			in.SourceName = strFlag(f, "source-name", &sourceName)
			in.PrepTimeMinutes = intFlag(f, "prep-time", &prepTime)
			in.CookTimeMinutes = intFlag(f, "cook-time", &cookTime)
			in.TotalTimeMinutes = intFlag(f, "total-time", &totalTime)
			in.Servings = intFlag(f, "servings", &servings)
			in.Difficulty = strFlag(f, "difficulty", &difficulty)
			in.Cuisine = strFlag(f, "cuisine", &cuisine)
			in.MealType = strFlag(f, "meal-type", &mealType)
			if f.Changed("tag") {
				in.Tags = tags
			}
			in.Notes = strFlag(f, "notes", &notes)
			in.Rating = intFlag(f, "rating", &rating)
			if f.Changed("ingredients-json") {
				ingredients, err := parseIngredientsJSON(ingredientsJSON)
				if err != nil {
					return err
				}
				in.Ingredients = &ingredients
			}

			if isEmptyRecipeUpdate(in) && len(clear) == 0 {
				return usageError{fmt.Errorf("nothing to change — pass at least one field flag or --clear")}
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			recipe, err := client.UpdateRecipe(cmd.Context(), id, in, clear)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), recipe)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Updated recipe %q (id %d)\n", recipe.Name, recipe.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "Recipe name")
	cmd.Flags().StringVar(&instructions, "instructions", "", "Instructions (markdown)")
	cmd.Flags().StringVar(&ingredientsJSON, "ingredients-json", "", "JSON array of ingredient objects (replaces the list)")
	cmd.Flags().IntVar(&servings, "servings", 0, "Number of servings")
	cmd.Flags().StringArrayVar(&clear, "clear", nil, "Field to set to null, e.g. --clear rating (repeatable, API field names)")
	addRecipeScalarFlags(cmd, &description, &sourceURL, &sourceName, &prepTime, &cookTime, &totalTime, &difficulty, &cuisine, &mealType, &tags, &notes, &rating)
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated recipe as JSON to stdout")
	return cmd
}

func newRecipesDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <recipe-id>",
		Short:   "Delete a recipe",
		Example: "  icb recipes delete 2 --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("recipe id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			recipe, err := client.GetRecipe(cmd.Context(), id, nil)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				ok, err := confirm(cmd.ErrOrStderr(), cmd.InOrStdin(),
					fmt.Sprintf("Delete recipe %q (id %d)?", recipe.Name, recipe.ID))
				if err != nil {
					return err
				}
				if !ok {
					fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteRecipe(cmd.Context(), id); err != nil {
				return handleAPIError(err)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Deleted recipe %q (id %d)\n", recipe.Name, id)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func newRecipesMadeCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "made <recipe-id>",
		Short:   "Mark a recipe made (bump times-made, stamp now)",
		Example: "  icb recipes made 2",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := parseIntArg("recipe id", args[0])
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			recipe, err := client.MarkRecipeMade(cmd.Context(), id)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), recipe)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Marked %q made (id %d, %d× total)\n", recipe.Name, recipe.ID, recipe.TimesMade)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated recipe as JSON to stdout")
	return cmd
}

func newRecipesAISuggestCommand() *cobra.Command {
	var (
		have   []string
		want   string
		count  int
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "ai-suggest --have <ingredient> [flags]",
		Short: "Ask Claude for recipe candidates from ingredients you have",
		Long: "Server-side Claude (with web search) returns candidates WITHOUT saving. Feed a\n" +
			"candidate object to `icb recipes ai-save --candidate-json <json>` to persist.\n" +
			"Slow (30-60s). Use --json to capture candidates for piping to ai-save.",
		Example: "  icb recipes ai-suggest --have chicken --have lemon --want \"quick weeknight dinner\"",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			if len(have) == 0 {
				return usageError{fmt.Errorf("--have is required (repeatable)")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			resp, err := client.AISuggestRecipes(cmd.Context(), have, strFlag(cmd.Flags(), "want", &want), count)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), resp)
			}
			printCandidates(cmd.OutOrStdout(), resp.Candidates)
			return nil
		},
	}
	cmd.Flags().StringArrayVar(&have, "have", nil, "Ingredient on hand (repeatable)")
	cmd.Flags().StringVar(&want, "want", "", "Free-form description of the dish you want")
	cmd.Flags().IntVar(&count, "count", 3, "Number of candidates to return")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the full suggestion response as JSON to stdout")
	return cmd
}

func newRecipesAISaveCommand() *cobra.Command {
	var (
		candidateJSON string
		asJSON        bool
	)
	cmd := &cobra.Command{
		Use:     "ai-save --candidate-json <json>",
		Short:   "Persist an AI recipe candidate",
		Long:    "Save a candidate object (one element from `ai-suggest`) to the recipe catalog.",
		Example: "  icb recipes ai-save --candidate-json \"$(cat candidate.json)\"",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			candidate, err := validJSONFlag("--candidate-json", candidateJSON)
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			recipe, err := client.AISaveRecipe(cmd.Context(), candidate)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), recipe)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Saved recipe %q (id %d)\n", recipe.Name, recipe.ID)
			return nil
		},
	}
	cmd.Flags().StringVar(&candidateJSON, "candidate-json", "", "Candidate object JSON (from ai-suggest)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the saved recipe as JSON to stdout")
	return cmd
}

func newRecipesAIImportCommand() *cobra.Command {
	var (
		hint   string
		asJSON bool
	)
	cmd := &cobra.Command{
		Use:   "ai-import <url>",
		Short: "Classify a URL into recipe/technique candidate(s)",
		Long: "Fetch and classify a YouTube or article URL, returning candidate(s) WITHOUT\n" +
			"saving. Feed the candidate to `icb recipes ai-save-import`. --hint forces a\n" +
			"kind: auto (default), recipe, technique, or both.",
		Example: "  icb recipes ai-import https://youtu.be/xyz --hint both --json",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if hint != "auto" && hint != "recipe" && hint != "technique" && hint != "both" {
				return usageError{fmt.Errorf("--hint must be auto, recipe, technique, or both")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			resp, err := client.AIImportFromURL(cmd.Context(), args[0], hint)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), resp)
			}
			printImportCandidate(cmd.OutOrStdout(), resp.Candidate)
			return nil
		},
	}
	cmd.Flags().StringVar(&hint, "hint", "auto", "Classification hint: auto, recipe, technique, or both")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the import response as JSON to stdout")
	return cmd
}

func newRecipesAISaveImportCommand() *cobra.Command {
	var (
		candidateJSON string
		asJSON        bool
	)
	cmd := &cobra.Command{
		Use:   "ai-save-import --candidate-json <json>",
		Short: "Persist a reviewed URL-import candidate",
		Long: "Save the candidate returned by `ai-import` (recipe and/or technique). For\n" +
			"kind=both, the technique_mention is appended to the recipe's notes.",
		Example: "  icb recipes ai-save-import --candidate-json \"$(cat candidate.json)\"",
		Args:    usageArgs(cobra.NoArgs),
		RunE: func(cmd *cobra.Command, _ []string) error {
			candidate, err := validJSONFlag("--candidate-json", candidateJSON)
			if err != nil {
				return err
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			result, err := client.AISaveURLImport(cmd.Context(), candidate)
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), result)
			}
			if result.Recipe != nil {
				fmt.Fprintf(cmd.OutOrStdout(), "Saved recipe %q (id %d)\n", result.Recipe.Name, result.Recipe.ID)
			}
			if result.Technique != nil {
				fmt.Fprintf(cmd.OutOrStdout(), "Saved technique %q (id %d)\n", result.Technique.Name, result.Technique.ID)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&candidateJSON, "candidate-json", "", "Candidate object JSON (from ai-import)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the save result as JSON to stdout")
	return cmd
}

// addRecipeScalarFlags registers the create/edit scalar flags shared by both so
// they stay in lockstep.
func addRecipeScalarFlags(cmd *cobra.Command, description, sourceURL, sourceName *string, prepTime, cookTime, totalTime *int, difficulty, cuisine, mealType *string, tags *[]string, notes *string, rating *int) {
	cmd.Flags().StringVar(description, "description", "", "Short description")
	cmd.Flags().StringVar(sourceURL, "source-url", "", "Source URL")
	cmd.Flags().StringVar(sourceName, "source-name", "", "Source name")
	cmd.Flags().IntVar(prepTime, "prep-time", 0, "Prep time in minutes")
	cmd.Flags().IntVar(cookTime, "cook-time", 0, "Cook time in minutes")
	cmd.Flags().IntVar(totalTime, "total-time", 0, "Total time in minutes")
	cmd.Flags().StringVar(difficulty, "difficulty", "", "Difficulty")
	cmd.Flags().StringVar(cuisine, "cuisine", "", "Cuisine")
	cmd.Flags().StringVar(mealType, "meal-type", "", "Meal type")
	cmd.Flags().StringArrayVar(tags, "tag", nil, "Tag (repeatable; replaces the tag list)")
	cmd.Flags().StringVar(notes, "notes", "", "Notes")
	cmd.Flags().IntVar(rating, "rating", 0, "Rating (1-5)")
}

// parseIngredientsJSON parses the --ingredients-json flag into ingredient inputs.
// An empty string yields an empty list (a recipe with no structured ingredients).
func parseIngredientsJSON(raw string) ([]api.RecipeIngredientInput, error) {
	if strings.TrimSpace(raw) == "" {
		return []api.RecipeIngredientInput{}, nil
	}
	var ingredients []api.RecipeIngredientInput
	if err := json.Unmarshal([]byte(raw), &ingredients); err != nil {
		return nil, usageError{fmt.Errorf("--ingredients-json is not a valid JSON array of ingredients: %w", err)}
	}
	return ingredients, nil
}

// validJSONFlag ensures a required JSON-blob flag is present and well-formed,
// returning it as raw bytes for verbatim POSTing.
func validJSONFlag(name, raw string) (json.RawMessage, error) {
	if strings.TrimSpace(raw) == "" {
		return nil, usageError{fmt.Errorf("%s is required", name)}
	}
	if !json.Valid([]byte(raw)) {
		return nil, usageError{fmt.Errorf("%s is not valid JSON", name)}
	}
	return json.RawMessage(raw), nil
}

func isEmptyRecipeUpdate(in api.RecipeUpdateInput) bool {
	return in.Name == nil && in.Instructions == nil && in.Description == nil && in.SourceURL == nil &&
		in.SourceName == nil && in.PrepTimeMinutes == nil && in.CookTimeMinutes == nil &&
		in.TotalTimeMinutes == nil && in.Servings == nil && in.Difficulty == nil && in.Cuisine == nil &&
		in.MealType == nil && in.Tags == nil && in.Notes == nil && in.Rating == nil && in.Ingredients == nil
}

func runRecipeList(cmd *cobra.Command, asJSON bool, fetch func(*api.Client) ([]api.Recipe, error)) error {
	client, err := newAPIClient(cmd.Context())
	if err != nil {
		return handleAPIError(err)
	}
	recipes, err := fetch(client)
	if err != nil {
		return handleAPIError(err)
	}
	if asJSON {
		return encodeJSON(cmd.OutOrStdout(), recipes)
	}
	printRecipesTable(cmd.OutOrStdout(), recipes)
	return nil
}

func printRecipesTable(out io.Writer, recipes []api.Recipe) {
	if len(recipes) == 0 {
		fmt.Fprintln(out, "No recipes.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tRATING\tCUISINE\tMEAL\tTIME\tMADE\tNAME")
	for _, r := range recipes {
		fmt.Fprintf(tw, "%d\t%s\t%s\t%s\t%s\t%d\t%s\n",
			r.ID, ratingStars(r.Rating), orNone(strValue(r.Cuisine)), orNone(strValue(r.MealType)),
			minutesLabel(r.TotalTimeMinutes), r.TimesMade, r.Name)
	}
	_ = tw.Flush()
}

func printIngredientSearchTable(out io.Writer, results []api.RecipeIngredientSearchResult) {
	if len(results) == 0 {
		fmt.Fprintln(out, "No matching recipes.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(tw, "ID\tMATCHED\tNAME")
	for _, r := range results {
		fmt.Fprintf(tw, "%d\t%d/%d\t%s\n", r.Recipe.ID, r.Coverage, r.TotalIngredients, r.Recipe.Name)
	}
	_ = tw.Flush()
}

func printRecipeDetail(out io.Writer, r api.Recipe) {
	fmt.Fprintf(out, "%s\n", r.Name)
	fmt.Fprintf(out, "  id:        %d\n", r.ID)
	fmt.Fprintf(out, "  rating:    %s\n", ratingStars(r.Rating))
	fmt.Fprintf(out, "  servings:  %d\n", r.Servings)
	fmt.Fprintf(out, "  cuisine:   %s\n", orNone(strValue(r.Cuisine)))
	fmt.Fprintf(out, "  meal:      %s\n", orNone(strValue(r.MealType)))
	fmt.Fprintf(out, "  time:      %s\n", minutesLabel(r.TotalTimeMinutes))
	fmt.Fprintf(out, "  made:      %d×\n", r.TimesMade)
	fmt.Fprintf(out, "  tags:      %s\n", orNone(strings.Join(r.Tags, ", ")))
	if s := strValue(r.SourceName); s != "" {
		fmt.Fprintf(out, "  source:    %s\n", s)
	}
	if s := strValue(r.Description); s != "" {
		fmt.Fprintf(out, "  desc:      %s\n", s)
	}
	fmt.Fprintln(out, "  ingredients:")
	for _, ing := range r.Ingredients {
		fmt.Fprintf(out, "    - %s\n", ingredientLine(ing))
	}
	fmt.Fprintf(out, "\n%s\n", r.Instructions)
	if s := strValue(r.Notes); s != "" {
		fmt.Fprintf(out, "\nnotes: %s\n", s)
	}
}

// ingredientLine renders one ingredient, preferring scaled_quantity when present.
func ingredientLine(ing api.RecipeIngredient) string {
	var b strings.Builder
	qty := ing.Quantity
	if ing.ScaledQuantity != nil {
		qty = ing.ScaledQuantity
	}
	if qty != nil {
		b.WriteString(strconv.FormatFloat(*qty, 'g', -1, 64))
		b.WriteByte(' ')
	}
	if u := strValue(ing.Unit); u != "" {
		b.WriteString(u)
		b.WriteByte(' ')
	}
	b.WriteString(ing.Item)
	if n := strValue(ing.PrepNote); n != "" {
		b.WriteString(", ")
		b.WriteString(n)
	}
	if ing.IsOptional {
		b.WriteString(" (optional)")
	}
	return b.String()
}

// printCandidates renders AI-suggested candidates: names for humans, with a
// pointer to --json for the full objects needed by ai-save.
func printCandidates(out io.Writer, candidates []json.RawMessage) {
	if len(candidates) == 0 {
		fmt.Fprintln(out, "No candidates.")
		return
	}
	fmt.Fprintf(out, "%d candidate(s):\n", len(candidates))
	for i, raw := range candidates {
		var peek struct {
			Name    string `json:"name"`
			Cuisine string `json:"cuisine"`
		}
		_ = json.Unmarshal(raw, &peek)
		fmt.Fprintf(out, "  %d. %s (%s)\n", i+1, peek.Name, orNone(peek.Cuisine))
	}
	fmt.Fprintln(out, "Re-run with --json to get the full candidate objects for `ai-save`.")
}

// printImportCandidate summarizes a URL-import candidate; the full object (needed
// by ai-save-import) comes from --json.
func printImportCandidate(out io.Writer, raw json.RawMessage) {
	var peek struct {
		Kind      string                 `json:"kind"`
		Recipe    *struct{ Name string } `json:"recipe"`
		Technique *struct{ Name string } `json:"technique"`
	}
	_ = json.Unmarshal(raw, &peek)
	fmt.Fprintf(out, "kind: %s\n", peek.Kind)
	if peek.Recipe != nil {
		fmt.Fprintf(out, "  recipe:    %s\n", peek.Recipe.Name)
	}
	if peek.Technique != nil {
		fmt.Fprintf(out, "  technique: %s\n", peek.Technique.Name)
	}
	fmt.Fprintln(out, "Re-run with --json to get the full candidate for `ai-save-import`.")
}

// minutesLabel renders an optional minute count.
func minutesLabel(minutes *int) string {
	if minutes == nil {
		return "-"
	}
	return fmt.Sprintf("%dm", *minutes)
}
