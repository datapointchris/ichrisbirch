package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestStrainFilter_QueryOmitsEmptyFields(t *testing.T) {
	cases := []struct {
		name   string
		filter StrainFilter
		limit  *int
		want   string
	}{
		{"zero value sends nothing", StrainFilter{}, nil, ""},
		{"one filter", StrainFilter{Status: "tried"}, nil, "status=tried"},
		{
			"every filter",
			StrainFilter{StrainType: "indica", Status: "tried", Effect: "sleepy", Flavor: "grape", RatingMin: 8},
			nil,
			"effect=sleepy&flavor=grape&rating_min=8&status=tried&strain_type=indica",
		},
		// A rating floor of zero is not a floor — every rating is at least 1 —
		// so it reads as unset rather than as a filter matching everything.
		{"rating_min zero is unset", StrainFilter{RatingMin: 0}, nil, ""},
		{"limit rides along", StrainFilter{Status: "tried"}, intPtr(3), "limit=3&status=tried"},
		// Zero rows is a real request and has to survive as limit=0, which a
		// falsy check would drop and answer with the whole collection.
		{"limit zero survives", StrainFilter{}, intPtr(0), "limit=0"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			var gotQuery string
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				gotQuery = r.URL.RawQuery
				w.Header().Set("Content-Type", "application/json")
				_, _ = w.Write([]byte(`[]`))
			}))
			defer srv.Close()

			client := New(srv.URL, staticTokenClient("t"))
			if _, err := client.ListStrains(context.Background(), tc.filter, tc.limit); err != nil {
				t.Fatalf("ListStrains: %v", err)
			}
			if gotQuery != tc.want {
				t.Errorf("query = %q, want %q", gotQuery, tc.want)
			}
		})
	}
}

func intPtr(n int) *int { return &n }

func TestCreateStrain_OmitsUnsetOptionalFields(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"name":"Runtz","status":"want_to_try","effects":[],"flavors":[],"terpenes":[],"tags":[]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	strain, err := client.CreateStrain(context.Background(), StrainCreateInput{Name: "Runtz"})
	if err != nil {
		t.Fatalf("CreateStrain: %v", err)
	}
	if gotBody["name"] != "Runtz" {
		t.Errorf("name = %v", gotBody["name"])
	}
	// An unset field must be absent, not null: the server reads absence as
	// "apply the default" and null as "this column is empty".
	for _, key := range []string{"breeder", "lineage", "strain_type", "status", "rating", "thc_percent", "effects"} {
		if _, present := gotBody[key]; present {
			t.Errorf("%s should be omitted when unset, body = %v", key, gotBody)
		}
	}
	if strain.Status != "want_to_try" {
		t.Errorf("strain = %+v", strain)
	}
}

func TestUpdateStrain_TellsApartLeaveAloneFromClear(t *testing.T) {
	cases := []struct {
		name        string
		in          StrainUpdateInput
		wantPresent bool
		wantValue   []any
	}{
		{"nil leaves the column alone", StrainUpdateInput{Name: strPtr("x")}, false, nil},
		{"empty slice clears it", StrainUpdateInput{Effects: &[]string{}}, true, []any{}},
		{"values replace it", StrainUpdateInput{Effects: &[]string{"sleepy"}}, true, []any{"sleepy"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			var gotBody map[string]any
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				raw, _ := io.ReadAll(r.Body)
				_ = json.Unmarshal(raw, &gotBody)
				w.Header().Set("Content-Type", "application/json")
				_, _ = w.Write([]byte(`{"id":1,"name":"x","status":"tried"}`))
			}))
			defer srv.Close()

			client := New(srv.URL, staticTokenClient("t"))
			if _, err := client.UpdateStrain(context.Background(), 1, tc.in); err != nil {
				t.Fatalf("UpdateStrain: %v", err)
			}
			got, present := gotBody["effects"]
			if present != tc.wantPresent {
				t.Fatalf("effects present = %v, want %v (body %v)", present, tc.wantPresent, gotBody)
			}
			if !tc.wantPresent {
				return
			}
			values, ok := got.([]any)
			if !ok || len(values) != len(tc.wantValue) {
				t.Fatalf("effects = %v, want %v", got, tc.wantValue)
			}
			for i, want := range tc.wantValue {
				if values[i] != want {
					t.Errorf("effects[%d] = %v, want %v", i, values[i], want)
				}
			}
		})
	}
}

func strPtr(s string) *string { return &s }

// last_tried_date is a calendar day, so it decodes as a string. Were it a
// time.Time, this row would fail and take the whole slice with it.
func TestListStrains_DecodesABareDayAndANullOne(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[
			{"id":1,"name":"Blue Dream","status":"tried","last_tried_date":"2026-03-14","effects":["relaxed"],"flavors":[],"terpenes":[],"tags":[]},
			{"id":2,"name":"Runtz","status":"want_to_try","last_tried_date":null,"effects":[],"flavors":[],"terpenes":[],"tags":[]}
		]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	strains, err := client.ListStrains(context.Background(), StrainFilter{}, nil)
	if err != nil {
		t.Fatalf("ListStrains: %v", err)
	}
	if len(strains) != 2 {
		t.Fatalf("got %d strains, want 2", len(strains))
	}
	if strains[0].LastTriedDate == nil || *strains[0].LastTriedDate != "2026-03-14" {
		t.Errorf("last_tried_date = %v, want 2026-03-14", strains[0].LastTriedDate)
	}
	if strains[1].LastTriedDate != nil {
		t.Errorf("a null day should decode as nil, got %v", *strains[1].LastTriedDate)
	}
}

func TestGetStrainVocabulary_KeepsValuesNothingUses(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/strains/vocabulary/" {
			t.Errorf("path = %q", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{
			"types":[{"name":"indica","count":2}],
			"statuses":[{"name":"tried","count":2},{"name":"want_to_try","count":0}],
			"effects":[{"name":"relaxed","count":2},{"name":"giggly","count":0}],
			"flavors":[],
			"terpenes":[]
		}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	vocabulary, err := client.GetStrainVocabulary(context.Background())
	if err != nil {
		t.Fatalf("GetStrainVocabulary: %v", err)
	}
	if names := VocabularyNames(vocabulary.Effects); len(names) != 2 || names[1] != "giggly" {
		t.Errorf("effect names = %v, want relaxed and giggly", names)
	}
	if vocabulary.Effects[1].Count != 0 {
		t.Errorf("giggly count = %d, want 0", vocabulary.Effects[1].Count)
	}
}
