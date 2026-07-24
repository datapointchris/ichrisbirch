package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListRecipes_Filters(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.Query().Encode()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":2,"name":"Amish Baked Oatmeal","servings":6,"tags":["breakfast"],"rating":5,"instructions":"mix","times_made":0,"last_made_date":null,"created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z","ingredients":[]}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	cuisine := "italian"
	ratingMin := 4
	maxTime := 45
	recipes, err := client.ListRecipes(context.Background(), &cuisine, nil, nil, &ratingMin, &maxTime)
	if err != nil {
		t.Fatalf("ListRecipes: %v", err)
	}
	if gotQuery != "cuisine=italian&max_total_time=45&rating_min=4" {
		t.Errorf("query = %q", gotQuery)
	}
	if len(recipes) != 1 || recipes[0].Servings != 6 || recipes[0].LastMadeDate != nil {
		t.Errorf("recipes = %+v", recipes)
	}

	_, _ = client.ListRecipes(context.Background(), nil, nil, nil, nil, nil)
	if gotQuery != "" {
		t.Errorf("query = %q, want empty", gotQuery)
	}
}

func TestGetRecipe_ServingsScaling(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.Query().Encode()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":2,"name":"R","servings":12,"tags":null,"instructions":"i","times_made":0,"created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z","ingredients":[{"position":0,"quantity":3.0,"unit":"cup","item":"oats","is_optional":false,"id":8,"recipe_id":2,"scaled_quantity":6.0}]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	servings := 12
	recipe, err := client.GetRecipe(context.Background(), 2, &servings)
	if err != nil {
		t.Fatalf("GetRecipe: %v", err)
	}
	if gotQuery != "servings=12" {
		t.Errorf("query = %q", gotQuery)
	}
	if len(recipe.Ingredients) != 1 || recipe.Ingredients[0].ScaledQuantity == nil || *recipe.Ingredients[0].ScaledQuantity != 6.0 {
		t.Errorf("ingredient = %+v", recipe.Ingredients)
	}
}

func TestSearchRecipesByIngredients_Decodes(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.Query().Encode()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"recipe":{"id":2,"name":"Amish Baked Oatmeal","servings":6,"tags":null,"instructions":"i","times_made":0,"created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z","ingredients":[]},"coverage":2,"total_ingredients":7}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	results, err := client.SearchRecipesByIngredients(context.Background(), "oats,milk", "all")
	if err != nil {
		t.Fatalf("SearchRecipesByIngredients: %v", err)
	}
	if gotQuery != "have=oats%2Cmilk&match=all" {
		t.Errorf("query = %q", gotQuery)
	}
	if len(results) != 1 || results[0].Coverage != 2 || results[0].TotalIngredients != 7 || results[0].Recipe.Name != "Amish Baked Oatmeal" {
		t.Errorf("results = %+v", results)
	}
}

func TestUpdateRecipe_ClearSendsExplicitNulls(t *testing.T) {
	var gotBody map[string]json.RawMessage
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":2,"name":"R","servings":4,"tags":null,"instructions":"i","times_made":0,"created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z","ingredients":[]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	name := "New Name"
	_, err := client.UpdateRecipe(context.Background(), 2, RecipeUpdateInput{Name: &name}, []string{"rating", "cuisine"})
	if err != nil {
		t.Fatalf("UpdateRecipe: %v", err)
	}
	if string(gotBody["name"]) != `"New Name"` {
		t.Errorf("name = %s", gotBody["name"])
	}
	if string(gotBody["rating"]) != "null" || string(gotBody["cuisine"]) != "null" {
		t.Errorf("cleared fields not null: rating=%s cuisine=%s", gotBody["rating"], gotBody["cuisine"])
	}
	// An unset, non-cleared field must not appear at all.
	if _, ok := gotBody["notes"]; ok {
		t.Errorf("notes should be absent, body = %v", gotBody)
	}
}

func TestAISuggestRecipes_KeepsCandidatesRaw(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"candidates":[{"name":"Lemon Chicken","source_url":"https://x","instructions":"cook","ingredients":[]}]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	want := "quick dinner"
	resp, err := client.AISuggestRecipes(context.Background(), []string{"chicken", "lemon"}, &want, 3)
	if err != nil {
		t.Fatalf("AISuggestRecipes: %v", err)
	}
	if gotBody["want"] != "quick dinner" || gotBody["count"] != float64(3) {
		t.Errorf("body = %v", gotBody)
	}
	if len(resp.Candidates) != 1 {
		t.Fatalf("candidates = %+v", resp.Candidates)
	}
	var peek struct {
		Name string `json:"name"`
	}
	if err := json.Unmarshal(resp.Candidates[0], &peek); err != nil || peek.Name != "Lemon Chicken" {
		t.Errorf("candidate raw = %s (%v)", resp.Candidates[0], err)
	}
}

func TestAISaveRecipe_PostsCandidateVerbatim(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":9,"name":"Lemon Chicken","servings":4,"tags":null,"instructions":"cook","times_made":0,"created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z","ingredients":[]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	candidate := json.RawMessage(`{"name":"Lemon Chicken","source_url":"https://x","instructions":"cook","ingredients":[]}`)
	recipe, err := client.AISaveRecipe(context.Background(), candidate)
	if err != nil {
		t.Fatalf("AISaveRecipe: %v", err)
	}
	if gotBody["source_url"] != "https://x" {
		t.Errorf("candidate not posted verbatim: %v", gotBody)
	}
	if recipe.ID != 9 {
		t.Errorf("recipe = %+v", recipe)
	}
}
