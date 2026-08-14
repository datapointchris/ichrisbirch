package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCreateProject_SendsPostBody(t *testing.T) {
	var gotMethod string
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":"018f-new","name":"New","description":null,"position":0,"created_at":"2026-07-24T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	desc := "a description"
	project, err := client.CreateProject(context.Background(), ProjectCreateInput{Name: "New", Description: &desc})
	if err != nil {
		t.Fatalf("CreateProject: %v", err)
	}

	if gotMethod != http.MethodPost {
		t.Errorf("method = %s, want POST", gotMethod)
	}
	if gotPath != "/projects/" {
		t.Errorf("path = %s, want /projects/", gotPath)
	}
	if gotBody["name"] != "New" || gotBody["description"] != "a description" {
		t.Errorf("body = %v", gotBody)
	}
	// position was not set, so omitempty must keep it out of the payload.
	if _, ok := gotBody["position"]; ok {
		t.Errorf("position should be omitted when unset, body = %v", gotBody)
	}
	if project.ID != "018f-new" {
		t.Errorf("returned project = %+v", project)
	}
}

func TestUpdateProject_SendsPatchPartialBody(t *testing.T) {
	var gotMethod string
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":"018f-a","name":"Renamed","description":null,"position":0,"created_at":"2026-07-24T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	name := "Renamed"
	_, err := client.UpdateProject(context.Background(), "018f-a", ProjectUpdateInput{Name: &name})
	if err != nil {
		t.Fatalf("UpdateProject: %v", err)
	}

	if gotMethod != http.MethodPatch {
		t.Errorf("method = %s, want PATCH", gotMethod)
	}
	if gotPath != "/projects/018f-a/" {
		t.Errorf("path = %s, want /projects/018f-a/", gotPath)
	}
	if gotBody["name"] != "Renamed" {
		t.Errorf("body = %v", gotBody)
	}
	// Only name was set; description/position must be omitted (partial update).
	if len(gotBody) != 1 {
		t.Errorf("partial update should send only changed fields, body = %v", gotBody)
	}
}

func TestProjectKind_OmittedWhenUnsetAndDecodedFromTheResponse(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(
			`{"id":"018f-new","name":"New","description":null,"kind":"build","position":0,"created_at":"2026-07-24T00:00:00Z"}`,
		))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	project, err := client.CreateProject(context.Background(), ProjectCreateInput{Name: "New"})
	if err != nil {
		t.Fatalf("CreateProject: %v", err)
	}

	// Unset means "let the server default it", so the field must not be sent —
	// an empty string would fail the lookup-table foreign key.
	if _, ok := gotBody["kind"]; ok {
		t.Errorf("kind should be omitted when unset, body = %v", gotBody)
	}
	if project.Kind != "build" {
		t.Errorf("kind = %q, want build from the response", project.Kind)
	}
}

func TestProjectKind_SentWhenSet(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(
			`{"id":"018f-a","name":"A","description":null,"kind":"chore","position":0,"created_at":"2026-07-24T00:00:00Z"}`,
		))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	kind := "chore"
	project, err := client.UpdateProject(context.Background(), "018f-a", ProjectUpdateInput{Kind: &kind})
	if err != nil {
		t.Fatalf("UpdateProject: %v", err)
	}

	if gotBody["kind"] != "chore" || len(gotBody) != 1 {
		t.Errorf("partial update should send kind alone, body = %v", gotBody)
	}
	if project.Kind != "chore" {
		t.Errorf("kind = %q, want chore", project.Kind)
	}
}

func TestDeleteProject_Sends204Delete(t *testing.T) {
	var gotMethod string
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		gotPath = r.URL.Path
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if err := client.DeleteProject(context.Background(), "018f-a"); err != nil {
		t.Fatalf("DeleteProject: %v", err)
	}
	if gotMethod != http.MethodDelete {
		t.Errorf("method = %s, want DELETE", gotMethod)
	}
	if gotPath != "/projects/018f-a/" {
		t.Errorf("path = %s, want /projects/018f-a/", gotPath)
	}
}

func TestListProjects_DecodesOpenAndCompletedCounts(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		// Two archived items, so the counts deliberately do not sum to item_count.
		_, _ = w.Write([]byte(`[
			{"id":"018f-a","name":"Personal OS","description":null,"kind":"build","position":0,"created_at":"2026-07-24T00:00:00Z","item_count":9,"open_count":3,"completed_count":4}
		]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	projects, err := client.ListProjects(context.Background(), nil, "")
	if err != nil {
		t.Fatalf("ListProjects: %v", err)
	}

	if len(projects) != 1 {
		t.Fatalf("got %d projects, want 1", len(projects))
	}
	p := projects[0]
	if p.OpenCount == nil || *p.OpenCount != 3 {
		t.Errorf("open_count = %v, want 3", p.OpenCount)
	}
	if p.CompletedCount == nil || *p.CompletedCount != 4 {
		t.Errorf("completed_count = %v, want 4", p.CompletedCount)
	}
}

func TestCreateProject_LeavesCountsNilWhenTheServerOmitsThem(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":"018f-new","name":"New","description":null,"kind":"build","position":0,"created_at":"2026-07-24T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	project, err := client.CreateProject(context.Background(), ProjectCreateInput{Name: "New"})
	if err != nil {
		t.Fatalf("CreateProject: %v", err)
	}

	// nil, not 0 — the create response says nothing about the counts, and a
	// rendered "0 open" would be a claim the server never made.
	if project.OpenCount != nil || project.CompletedCount != nil || project.ItemCount != nil {
		t.Errorf("counts = %v/%v/%v, want all nil", project.ItemCount, project.OpenCount, project.CompletedCount)
	}
}

func TestListProjectItems_StatusQueryParam(t *testing.T) {
	var gotPath string
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":"item-1","title":"First","notes":null,"completed":false,"archived":false,"created_at":"2026-07-24T00:00:00Z","updated_at":"2026-07-24T00:00:00Z","position":0}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))

	items, err := client.ListProjectItems(context.Background(), "018f-a", "all")
	if err != nil {
		t.Fatalf("ListProjectItems: %v", err)
	}
	if gotPath != "/projects/018f-a/items/" {
		t.Errorf("path = %s, want /projects/018f-a/items/", gotPath)
	}
	if gotQuery != "status=all" {
		t.Errorf("query = %q, want status=all", gotQuery)
	}
	if len(items) != 1 || items[0].Title != "First" {
		t.Errorf("items = %+v", items)
	}

	// An empty status sends nothing, leaving the server's default rather than
	// spelling it client-side where it would drift from the API.
	_, _ = client.ListProjectItems(context.Background(), "018f-a", "")
	if gotQuery != "" {
		t.Errorf("query = %q, want empty when no status is given", gotQuery)
	}
}

func TestListProjects_OmitsTheStatusParamWhenUnset(t *testing.T) {
	// The server's own default is the active projects; sending status=active
	// would make the CLI the place that decision lives.
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListProjects(context.Background(), nil, ""); err != nil {
		t.Fatalf("ListProjects: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want no parameters", *query)
	}
}

func TestListProjects_SendsTheStatusParam(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListProjects(context.Background(), nil, AllProjectStatuses); err != nil {
		t.Fatalf("ListProjects: %v", err)
	}
	if *query != "status=all" {
		t.Errorf("query = %q, want status=all", *query)
	}
}

func TestListProjects_DecodesTheClosure(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[
			{"id":"018f-a","name":"Rewrite in Rust","description":null,"kind":"build","status":"dropped","status_reason":"Go covers it","closed_at":"2026-08-01T12:00:00Z","position":0,"created_at":"2026-07-24T00:00:00Z","item_count":3,"open_count":1,"completed_count":2}
		]`))
	}))
	defer srv.Close()

	projects, err := New(srv.URL, staticTokenClient("t")).ListProjects(context.Background(), nil, AllProjectStatuses)
	if err != nil {
		t.Fatalf("ListProjects: %v", err)
	}
	p := projects[0]
	if p.Status != "dropped" {
		t.Errorf("status = %q, want dropped", p.Status)
	}
	if p.StatusReason == nil || *p.StatusReason != "Go covers it" {
		t.Errorf("status_reason = %v, want the reason it was dropped", p.StatusReason)
	}
	if p.ClosedAt == nil || p.ClosedAt.Year() != 2026 {
		t.Errorf("closed_at = %v, want the closing timestamp", p.ClosedAt)
	}
	if p.OpenCount == nil || *p.OpenCount != 1 {
		t.Errorf("open_count = %v — closing a project must not zero its open items", p.OpenCount)
	}
}

func TestProject_LeavesTheClosureNilWhileActive(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":"018f-a","name":"Live","description":null,"kind":"build","status":"active","status_reason":null,"closed_at":null,"position":0,"created_at":"2026-07-24T00:00:00Z","item_count":0,"open_count":0,"completed_count":0}`))
	}))
	defer srv.Close()

	project, err := New(srv.URL, staticTokenClient("t")).GetProject(context.Background(), "018f-a")
	if err != nil {
		t.Fatalf("GetProject: %v", err)
	}
	if project.ClosedAt != nil || project.StatusReason != nil {
		t.Errorf("an active project carries no closure, got closed_at=%v reason=%v", project.ClosedAt, project.StatusReason)
	}
}
