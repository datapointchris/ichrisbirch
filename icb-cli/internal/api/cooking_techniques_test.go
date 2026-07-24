package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListCookingTechniques_Filters(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.Query().Encode()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":3,"name":"24-Hour Bean Soak","category":"preservation_and_pre_treatment","summary":"s","body":"b","why_it_works":"w","common_pitfalls":null,"source_url":null,"source_name":null,"tags":["beans"],"rating":5,"slug":"24-hour-bean-soak","created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z"}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	cat := "flavor_development"
	min := 4
	techniques, err := client.ListCookingTechniques(context.Background(), &cat, &min)
	if err != nil {
		t.Fatalf("ListCookingTechniques: %v", err)
	}
	if gotQuery != "category=flavor_development&rating_min=4" {
		t.Errorf("query = %q", gotQuery)
	}
	if len(techniques) != 1 || techniques[0].Slug != "24-hour-bean-soak" {
		t.Fatalf("techniques = %+v", techniques)
	}
	tq := techniques[0]
	if tq.CommonPitfalls != nil || tq.Rating == nil || *tq.Rating != 5 {
		t.Errorf("nullable decode = %+v", tq)
	}

	// nil filters → no query string.
	_, _ = client.ListCookingTechniques(context.Background(), nil, nil)
	if gotQuery != "" {
		t.Errorf("query = %q, want empty", gotQuery)
	}
}

func TestGetCookingTechniqueBySlug_EscapesSlug(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.EscapedPath()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":3,"name":"N","category":"c","summary":"s","body":"b","tags":null,"slug":"24-hour-bean-soak","created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	technique, err := client.GetCookingTechniqueBySlug(context.Background(), "24-hour-bean-soak")
	if err != nil {
		t.Fatalf("GetCookingTechniqueBySlug: %v", err)
	}
	if gotPath != "/recipes/cooking-techniques/slug/24-hour-bean-soak/" {
		t.Errorf("path = %s", gotPath)
	}
	if technique.ID != 3 || technique.Tags != nil {
		t.Errorf("technique = %+v", technique)
	}
}

func TestCreateCookingTechnique_OmitsUnsetOptionals(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":9,"name":"Bloom Spices","category":"flavor_development","summary":"s","body":"b","tags":null,"slug":"bloom-spices","created_at":"2026-07-24T14:33:26Z","updated_at":"2026-07-24T14:33:26Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	created, err := client.CreateCookingTechnique(context.Background(), CookingTechniqueCreateInput{
		Name: "Bloom Spices", Category: "flavor_development", Summary: "s", Body: "b",
	})
	if err != nil {
		t.Fatalf("CreateCookingTechnique: %v", err)
	}
	if _, ok := gotBody["why_it_works"]; ok {
		t.Errorf("unset optional why_it_works should be omitted, body = %v", gotBody)
	}
	if _, ok := gotBody["rating"]; ok {
		t.Errorf("unset rating should be omitted, body = %v", gotBody)
	}
	if created.Slug != "bloom-spices" {
		t.Errorf("created = %+v", created)
	}
}

func TestListCookingTechniqueCategories_Decodes(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"name":"flavor_development","count":3},{"name":"dough_and_batter","count":0}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	categories, err := client.ListCookingTechniqueCategories(context.Background())
	if err != nil {
		t.Fatalf("ListCookingTechniqueCategories: %v", err)
	}
	if len(categories) != 2 || categories[0].Count != 3 || categories[1].Count != 0 {
		t.Errorf("categories = %+v", categories)
	}
}
