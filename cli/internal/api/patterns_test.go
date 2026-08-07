package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCreatePattern_OmitsRecordedAtWhenUnset(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"message":"coffee at 3pm","recorded_at":"2026-08-07T15:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.CreatePattern(context.Background(), PatternCreateInput{Message: "coffee at 3pm"}); err != nil {
		t.Fatalf("CreatePattern: %v", err)
	}
	// Sending an explicit null would override the server default and fail
	// validation, so the field has to be absent rather than empty.
	if _, present := gotBody["recorded_at"]; present {
		t.Errorf("recorded_at was sent (%v); the API stamps now when it is absent", gotBody["recorded_at"])
	}
}

func TestCreatePattern_SendsRecordedAtWhenSet(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"message":"imported","recorded_at":"2025-12-11T22:34:40Z"}`))
	}))
	defer srv.Close()

	at := "2025-12-11T22:34:40Z"
	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.CreatePattern(context.Background(), PatternCreateInput{Message: "imported", RecordedAt: &at}); err != nil {
		t.Fatalf("CreatePattern: %v", err)
	}
	if gotBody["recorded_at"] != at {
		t.Errorf("recorded_at = %v, want %s", gotBody["recorded_at"], at)
	}
}

func TestListPatterns_EncodesSearchAndLimit(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.ListPatterns(context.Background(), PatternListOptions{Search: "heart burn", Limit: 5}); err != nil {
		t.Fatalf("ListPatterns: %v", err)
	}
	if gotQuery != "limit=5&search=heart+burn" {
		t.Errorf("query = %q", gotQuery)
	}
}

func TestListPatterns_OmitsEmptyFilters(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.ListPatterns(context.Background(), PatternListOptions{}); err != nil {
		t.Fatalf("ListPatterns: %v", err)
	}
	if gotQuery != "" {
		t.Errorf("query = %q, want empty", gotQuery)
	}
}
