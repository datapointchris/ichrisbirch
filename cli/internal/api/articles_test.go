package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListArticles_TriStateFilters(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":1,"title":"A","url":"https://x","tags":["db"],"summary":"s","read_count":0,"is_favorite":false,"is_current":false,"is_archived":false,"save_date":"2026-01-01T00:00:00Z"}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	unread := true
	articles, err := client.ListArticles(context.Background(), nil, nil, &unread)
	if err != nil {
		t.Fatalf("ListArticles: %v", err)
	}
	if gotQuery != "unread=true" {
		t.Errorf("query = %q, want only unread=true when other filters are nil", gotQuery)
	}
	if len(articles) != 1 || articles[0].Tags[0] != "db" {
		t.Errorf("articles = %+v", articles)
	}

	favorites := false
	archived := true
	_, _ = client.ListArticles(context.Background(), &favorites, &archived, nil)
	if gotQuery != "archived=true&favorites=false" {
		t.Errorf("query = %q, want both non-nil filters encoded", gotQuery)
	}

	_, _ = client.ListArticles(context.Background(), nil, nil, nil)
	if gotQuery != "" {
		t.Errorf("query = %q, want empty when all filters are nil", gotQuery)
	}
}

func TestGetCurrentArticle_NullIsNilNotError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`null`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	article, err := client.GetCurrentArticle(context.Background())
	if err != nil {
		t.Fatalf("GetCurrentArticle: %v", err)
	}
	if article != nil {
		t.Errorf("article = %+v, want nil for JSON null", article)
	}
}

func TestGetCurrentArticle_Present(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":7,"title":"Now","url":"https://x","tags":[],"summary":"s","read_count":1,"is_favorite":false,"is_current":true,"is_archived":false,"save_date":"2026-01-01T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	article, err := client.GetCurrentArticle(context.Background())
	if err != nil {
		t.Fatalf("GetCurrentArticle: %v", err)
	}
	if article == nil || article.ID != 7 || !article.IsCurrent {
		t.Errorf("article = %+v", article)
	}
}

func TestCreateArticleFromURL_SendsURLOmitsUnsetNotes(t *testing.T) {
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"title":"A","url":"https://x","tags":[],"summary":"s","read_count":0,"is_favorite":false,"is_current":false,"is_archived":false,"save_date":"2026-01-01T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.CreateArticleFromURL(context.Background(), ArticleCreateFromURLInput{URL: "https://x"}); err != nil {
		t.Fatalf("CreateArticleFromURL: %v", err)
	}
	if gotPath != "/articles/create-from-url/" {
		t.Errorf("path = %s", gotPath)
	}
	if gotBody["url"] != "https://x" {
		t.Errorf("url = %v", gotBody["url"])
	}
	if _, present := gotBody["notes"]; present {
		t.Errorf("notes should be omitted when unset, body = %v", gotBody)
	}
}

func TestUpdateArticle_PatchOmitsUnset(t *testing.T) {
	var gotMethod string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":1,"title":"A","url":"https://x","tags":[],"summary":"s","read_count":2,"is_favorite":true,"is_current":false,"is_archived":true,"save_date":"2026-01-01T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	favorite := true
	if _, err := client.UpdateArticle(context.Background(), 1, ArticleUpdateInput{IsFavorite: &favorite}); err != nil {
		t.Fatalf("UpdateArticle: %v", err)
	}
	if gotMethod != http.MethodPatch {
		t.Errorf("method = %s, want PATCH", gotMethod)
	}
	if gotBody["is_favorite"] != true {
		t.Errorf("is_favorite = %v", gotBody["is_favorite"])
	}
	// Unset fields must be omitted, not sent as nulls/zeros.
	for _, k := range []string{"title", "summary", "read_count", "review_days", "is_archived"} {
		if _, present := gotBody[k]; present {
			t.Errorf("%s should be omitted when unset, body = %v", k, gotBody)
		}
	}
}

func TestSearchArticles_EncodesQuery(t *testing.T) {
	var gotPath, gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.SearchArticles(context.Background(), "python,databases"); err != nil {
		t.Fatalf("SearchArticles: %v", err)
	}
	if gotPath != "/articles/search/" {
		t.Errorf("path = %s", gotPath)
	}
	if gotQuery != "q=python%2Cdatabases" {
		t.Errorf("query = %q", gotQuery)
	}
}

func TestDeleteArticle_Sends204NoBody(t *testing.T) {
	var gotMethod string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if err := client.DeleteArticle(context.Background(), 1); err != nil {
		t.Fatalf("DeleteArticle: %v", err)
	}
	if gotMethod != http.MethodDelete {
		t.Errorf("method = %s, want DELETE", gotMethod)
	}
}

func TestBulkImportArticles_PostsURLs(t *testing.T) {
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusAccepted)
		_, _ = w.Write([]byte(`{"batch_id":"abc-123","total":2,"status":"queued"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	batch, err := client.BulkImportArticles(context.Background(), []string{"https://a.com", "https://b.com"})
	if err != nil {
		t.Fatalf("BulkImportArticles: %v", err)
	}
	if gotPath != "/articles/bulk-import/" {
		t.Errorf("path = %s", gotPath)
	}
	urls, _ := gotBody["urls"].([]any)
	if len(urls) != 2 {
		t.Errorf("urls = %v", gotBody["urls"])
	}
	if batch.BatchID != "abc-123" || batch.Total != 2 || batch.Status != "queued" {
		t.Errorf("batch = %+v", batch)
	}
}

func TestBulkImportStatus_DecodesNaiveTimestamps(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.EscapedPath() // Path is decoded; EscapedPath shows the wire form.
		w.Header().Set("Content-Type", "application/json")
		// created_at/updated_at are naive (no timezone) — must decode as strings.
		_, _ = w.Write([]byte(`{"batch_id":"abc 123","status":"completed","total":2,"processed":2,"succeeded":1,"failed_count":1,"errors":[{"url":"https://b.com","error":"404 Not Found\nsee docs"}],"results":[{"url":"https://a.com","title":"A Post"}],"created_at":"2026-07-24T14:39:51.432465","updated_at":"2026-07-24T14:39:52.116682"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	status, err := client.BulkImportStatus(context.Background(), "abc 123")
	if err != nil {
		t.Fatalf("BulkImportStatus: %v", err)
	}
	if gotPath != "/articles/bulk-import/abc%20123/" {
		t.Errorf("path = %q (batch id must be path-escaped)", gotPath)
	}
	if status.Succeeded != 1 || status.FailedCount != 1 {
		t.Errorf("status = %+v", status)
	}
	if len(status.Results) != 1 || status.Results[0].Title != "A Post" {
		t.Errorf("results = %+v", status.Results)
	}
	if len(status.Errors) != 1 || status.Errors[0].URL != "https://b.com" {
		t.Errorf("errors = %+v", status.Errors)
	}
	if status.CreatedAt != "2026-07-24T14:39:51.432465" {
		t.Errorf("created_at = %q", status.CreatedAt)
	}
}

func TestListFailedArticleImports_DecodesRows(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":2,"url":"https://b.com","batch_id":"abc-123","error_message":"404 Not Found\nsee docs","failed_at":"2026-07-24T14:39:52.113047Z"}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	failed, err := client.ListFailedArticleImports(context.Background())
	if err != nil {
		t.Fatalf("ListFailedArticleImports: %v", err)
	}
	if len(failed) != 1 {
		t.Fatalf("failed = %+v", failed)
	}
	f := failed[0]
	if f.ID != 2 || f.BatchID == nil || *f.BatchID != "abc-123" || f.FailedAt.IsZero() {
		t.Errorf("failed[0] = %+v", f)
	}
}
