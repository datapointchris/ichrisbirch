package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

// RecipeIngredient mirrors an ingredient row on a recipe. scaled_quantity is
// populated only when the recipe was fetched with a servings override.
type RecipeIngredient struct {
	Position        int      `json:"position"`
	Quantity        *float64 `json:"quantity"`
	Unit            *string  `json:"unit"`
	Item            string   `json:"item"`
	PrepNote        *string  `json:"prep_note"`
	IsOptional      bool     `json:"is_optional"`
	IngredientGroup *string  `json:"ingredient_group"`
	ID              int      `json:"id"`
	RecipeID        int      `json:"recipe_id"`
	ScaledQuantity  *float64 `json:"scaled_quantity"`
}

// Recipe mirrors the recipes JSON — a full recipe with structured ingredients.
// Nullable scalar fields are pointers.
type Recipe struct {
	ID               int                `json:"id"`
	Name             string             `json:"name"`
	Description      *string            `json:"description"`
	SourceURL        *string            `json:"source_url"`
	SourceName       *string            `json:"source_name"`
	PrepTimeMinutes  *int               `json:"prep_time_minutes"`
	CookTimeMinutes  *int               `json:"cook_time_minutes"`
	TotalTimeMinutes *int               `json:"total_time_minutes"`
	Servings         int                `json:"servings"`
	Difficulty       *string            `json:"difficulty"`
	Cuisine          *string            `json:"cuisine"`
	MealType         *string            `json:"meal_type"`
	Tags             []string           `json:"tags"`
	Instructions     string             `json:"instructions"`
	Notes            *string            `json:"notes"`
	Rating           *int               `json:"rating"`
	TimesMade        int                `json:"times_made"`
	LastMadeDate     *time.Time         `json:"last_made_date"`
	CreatedAt        time.Time          `json:"created_at"`
	UpdatedAt        time.Time          `json:"updated_at"`
	Ingredients      []RecipeIngredient `json:"ingredients"`
}

// RecipeIngredientInput is one ingredient in a create/update body — the shape the
// CLI parses out of --ingredients-json.
type RecipeIngredientInput struct {
	Position        int      `json:"position"`
	Quantity        *float64 `json:"quantity"`
	Unit            *string  `json:"unit"`
	Item            string   `json:"item"`
	PrepNote        *string  `json:"prep_note"`
	IsOptional      bool     `json:"is_optional"`
	IngredientGroup *string  `json:"ingredient_group"`
}

// RecipeCreateInput is the body for POST /recipes/. name and instructions are
// required; servings defaults to 4 (always sent). ingredients may be empty.
type RecipeCreateInput struct {
	Name             string                  `json:"name"`
	Instructions     string                  `json:"instructions"`
	Ingredients      []RecipeIngredientInput `json:"ingredients"`
	Servings         int                     `json:"servings"`
	Description      *string                 `json:"description,omitempty"`
	SourceURL        *string                 `json:"source_url,omitempty"`
	SourceName       *string                 `json:"source_name,omitempty"`
	PrepTimeMinutes  *int                    `json:"prep_time_minutes,omitempty"`
	CookTimeMinutes  *int                    `json:"cook_time_minutes,omitempty"`
	TotalTimeMinutes *int                    `json:"total_time_minutes,omitempty"`
	Difficulty       *string                 `json:"difficulty,omitempty"`
	Cuisine          *string                 `json:"cuisine,omitempty"`
	MealType         *string                 `json:"meal_type,omitempty"`
	Tags             []string                `json:"tags,omitempty"`
	Notes            *string                 `json:"notes,omitempty"`
	Rating           *int                    `json:"rating,omitempty"`
}

// RecipeUpdateInput is a partial update (PATCH /recipes/{id}/): only set fields
// are sent. Ingredients, when non-nil, replaces the whole ingredient list.
type RecipeUpdateInput struct {
	Name             *string                  `json:"name,omitempty"`
	Instructions     *string                  `json:"instructions,omitempty"`
	Description      *string                  `json:"description,omitempty"`
	SourceURL        *string                  `json:"source_url,omitempty"`
	SourceName       *string                  `json:"source_name,omitempty"`
	PrepTimeMinutes  *int                     `json:"prep_time_minutes,omitempty"`
	CookTimeMinutes  *int                     `json:"cook_time_minutes,omitempty"`
	TotalTimeMinutes *int                     `json:"total_time_minutes,omitempty"`
	Servings         *int                     `json:"servings,omitempty"`
	Difficulty       *string                  `json:"difficulty,omitempty"`
	Cuisine          *string                  `json:"cuisine,omitempty"`
	MealType         *string                  `json:"meal_type,omitempty"`
	Tags             []string                 `json:"tags,omitempty"`
	Notes            *string                  `json:"notes,omitempty"`
	Rating           *int                     `json:"rating,omitempty"`
	Ingredients      *[]RecipeIngredientInput `json:"ingredients,omitempty"`
}

// RecipeIngredientSearchResult pairs a recipe with how many of the searched
// ingredients it matched.
type RecipeIngredientSearchResult struct {
	Recipe           Recipe `json:"recipe"`
	Coverage         int    `json:"coverage"`
	TotalIngredients int    `json:"total_ingredients"`
}

// RecipeSuggestionResponse wraps the AI-suggested candidates. Each candidate is
// kept as raw JSON — it round-trips to `ai-save` verbatim, so the CLI never has
// to model the full candidate shape.
type RecipeSuggestionResponse struct {
	Candidates []json.RawMessage `json:"candidates"`
}

// UrlImportResponse wraps the classifier's candidate (recipe and/or technique),
// kept raw so it round-trips to `ai-save-import` verbatim.
type UrlImportResponse struct {
	Candidate json.RawMessage `json:"candidate"`
}

// UrlImportSaveResult is what the save endpoint returns after persisting a URL
// import — either or both of a recipe and a technique.
type UrlImportSaveResult struct {
	Recipe    *Recipe           `json:"recipe"`
	Technique *CookingTechnique `json:"technique"`
}

// ListRecipes returns recipes ordered by name (GET /recipes/). Non-nil filters
// add query params.
func (c *Client) ListRecipes(ctx context.Context, cuisine, mealType, difficulty *string, ratingMin, maxTotalTime *int) ([]Recipe, error) {
	params := url.Values{}
	if cuisine != nil {
		params.Set("cuisine", *cuisine)
	}
	if mealType != nil {
		params.Set("meal_type", *mealType)
	}
	if difficulty != nil {
		params.Set("difficulty", *difficulty)
	}
	if ratingMin != nil {
		params.Set("rating_min", strconv.Itoa(*ratingMin))
	}
	if maxTotalTime != nil {
		params.Set("max_total_time", strconv.Itoa(*maxTotalTime))
	}
	path := "/recipes/"
	if encoded := params.Encode(); encoded != "" {
		path += "?" + encoded
	}
	var recipes []Recipe
	if err := c.get(ctx, path, &recipes); err != nil {
		return nil, err
	}
	return recipes, nil
}

// GetRecipe returns a single recipe (GET /recipes/{id}/). A non-nil servings
// scales each ingredient's scaled_quantity. Missing is 404.
func (c *Client) GetRecipe(ctx context.Context, id int, servings *int) (Recipe, error) {
	path := fmt.Sprintf("/recipes/%d/", id)
	if servings != nil {
		path += "?" + url.Values{"servings": {strconv.Itoa(*servings)}}.Encode()
	}
	var recipe Recipe
	if err := c.get(ctx, path, &recipe); err != nil {
		return Recipe{}, err
	}
	return recipe, nil
}

// SearchRecipes returns recipes matching q across name, instructions, and tags
// (GET /recipes/search/?q=).
func (c *Client) SearchRecipes(ctx context.Context, q string) ([]Recipe, error) {
	path := "/recipes/search/?" + url.Values{"q": {q}}.Encode()
	var recipes []Recipe
	if err := c.get(ctx, path, &recipes); err != nil {
		return nil, err
	}
	return recipes, nil
}

// SearchRecipesByIngredients ranks recipes by how many of the have-list
// ingredients they contain (GET /recipes/search-by-ingredients/). match is
// "any" (rank by coverage) or "all" (require every ingredient).
func (c *Client) SearchRecipesByIngredients(ctx context.Context, have, match string) ([]RecipeIngredientSearchResult, error) {
	path := "/recipes/search-by-ingredients/?" + url.Values{"have": {have}, "match": {match}}.Encode()
	var results []RecipeIngredientSearchResult
	if err := c.get(ctx, path, &results); err != nil {
		return nil, err
	}
	return results, nil
}

// CreateRecipe creates a recipe with structured ingredients (POST /recipes/).
func (c *Client) CreateRecipe(ctx context.Context, in RecipeCreateInput) (Recipe, error) {
	var recipe Recipe
	if err := c.send(ctx, http.MethodPost, "/recipes/", in, &recipe); err != nil {
		return Recipe{}, err
	}
	return recipe, nil
}

// UpdateRecipe applies a partial update (PATCH /recipes/{id}/). Each field named
// in clear is sent as an explicit null (the API's null_fields capability),
// covering numeric fields that an empty string cannot clear.
func (c *Client) UpdateRecipe(ctx context.Context, id int, in RecipeUpdateInput, clear []string) (Recipe, error) {
	body, err := mergeClearNulls(in, clear)
	if err != nil {
		return Recipe{}, err
	}
	var recipe Recipe
	if err := c.send(ctx, http.MethodPatch, fmt.Sprintf("/recipes/%d/", id), body, &recipe); err != nil {
		return Recipe{}, err
	}
	return recipe, nil
}

// DeleteRecipe removes a recipe (DELETE /recipes/{id}/ → 204).
func (c *Client) DeleteRecipe(ctx context.Context, id int) error {
	return c.send(ctx, http.MethodDelete, fmt.Sprintf("/recipes/%d/", id), nil, nil)
}

// MarkRecipeMade increments times_made and stamps last_made_date now (POST
// /recipes/{id}/mark-made/).
func (c *Client) MarkRecipeMade(ctx context.Context, id int) (Recipe, error) {
	var recipe Recipe
	if err := c.send(ctx, http.MethodPost, fmt.Sprintf("/recipes/%d/mark-made/", id), nil, &recipe); err != nil {
		return Recipe{}, err
	}
	return recipe, nil
}

// AISuggestRecipes asks the server-side Claude (with web search) for recipe
// candidates matching the have-list (POST /recipes/ai-suggest/). Nothing is
// saved — feed a candidate to AISaveRecipe to persist. Slow (web search).
func (c *Client) AISuggestRecipes(ctx context.Context, have []string, want *string, count int) (RecipeSuggestionResponse, error) {
	body := map[string]any{"have": have, "count": count}
	if want != nil {
		body["want"] = *want
	}
	var resp RecipeSuggestionResponse
	if err := c.send(ctx, http.MethodPost, "/recipes/ai-suggest/", body, &resp); err != nil {
		return RecipeSuggestionResponse{}, err
	}
	return resp, nil
}

// AISaveRecipe persists an AI candidate (POST /recipes/ai-save/). candidate is
// the raw candidate JSON, sent verbatim.
func (c *Client) AISaveRecipe(ctx context.Context, candidate json.RawMessage) (Recipe, error) {
	var recipe Recipe
	if err := c.send(ctx, http.MethodPost, "/recipes/ai-save/", candidate, &recipe); err != nil {
		return Recipe{}, err
	}
	return recipe, nil
}

// AIImportFromURL classifies a URL and returns recipe/technique candidate(s)
// without saving (POST /recipes/import-from-url/). hint is auto/recipe/
// technique/both.
func (c *Client) AIImportFromURL(ctx context.Context, importURL, hint string) (UrlImportResponse, error) {
	body := map[string]any{"url": importURL, "hint": hint}
	var resp UrlImportResponse
	if err := c.send(ctx, http.MethodPost, "/recipes/import-from-url/", body, &resp); err != nil {
		return UrlImportResponse{}, err
	}
	return resp, nil
}

// AISaveURLImport persists a reviewed URL-import candidate (POST
// /recipes/save-url-import/). candidate is the raw candidate JSON, sent verbatim.
func (c *Client) AISaveURLImport(ctx context.Context, candidate json.RawMessage) (UrlImportSaveResult, error) {
	var result UrlImportSaveResult
	if err := c.send(ctx, http.MethodPost, "/recipes/save-url-import/", candidate, &result); err != nil {
		return UrlImportSaveResult{}, err
	}
	return result, nil
}

// mergeClearNulls marshals a typed partial-update body to a JSON object and adds
// an explicit null for each field named in clear (API JSON keys). This is the
// wire form of the MCP null_fields param — the only way to clear a field the
// typed omitempty struct would otherwise drop.
func mergeClearNulls(input any, clear []string) (map[string]json.RawMessage, error) {
	raw, err := json.Marshal(input)
	if err != nil {
		return nil, err
	}
	body := map[string]json.RawMessage{}
	if err := json.Unmarshal(raw, &body); err != nil {
		return nil, err
	}
	for _, field := range clear {
		body[field] = json.RawMessage("null")
	}
	return body, nil
}
