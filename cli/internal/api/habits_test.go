package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListHabits_CurrentAndLimitQuery(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.Query().Encode()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":1,"name":"Stretch","category_id":2,"category":{"id":2,"name":"Health","is_current":true},"is_current":true}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))

	current := true
	limit := 3
	habits, err := client.ListHabits(context.Background(), &current, &limit)
	if err != nil {
		t.Fatalf("ListHabits: %v", err)
	}
	if gotQuery != "current=true&limit=3" {
		t.Errorf("query = %q", gotQuery)
	}
	if len(habits) != 1 || habits[0].Category.Name != "Health" {
		t.Errorf("habits = %+v", habits)
	}

	// current=false must still be sent (distinct from nil = omitted).
	no := false
	_, _ = client.ListHabits(context.Background(), &no, nil)
	if gotQuery != "current=false" {
		t.Errorf("query = %q, want current=false", gotQuery)
	}

	// nil current + nil limit → no query string.
	_, _ = client.ListHabits(context.Background(), nil, nil)
	if gotQuery != "" {
		t.Errorf("query = %q, want empty", gotQuery)
	}
}

func TestCompleteHabit_PostsCompletion(t *testing.T) {
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":9,"name":"Stretch","category_id":2,"category":{"id":2,"name":"Health","is_current":true},"complete_date":"2026-07-24T10:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	completed, err := client.CompleteHabit(context.Background(), HabitCompletedCreateInput{Name: "Stretch", CategoryID: 2, CompleteDate: "2026-07-24T10:00:00Z"})
	if err != nil {
		t.Fatalf("CompleteHabit: %v", err)
	}
	if gotPath != "/habits/completed/" {
		t.Errorf("path = %s", gotPath)
	}
	if gotBody["name"] != "Stretch" || gotBody["category_id"] != float64(2) {
		t.Errorf("body = %v", gotBody)
	}
	if completed.ID != 9 || completed.CompleteDate.IsZero() {
		t.Errorf("completed = %+v", completed)
	}
}
