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

func TestListProjectItems_ArchivedQueryParam(t *testing.T) {
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

	items, err := client.ListProjectItems(context.Background(), "018f-a", true)
	if err != nil {
		t.Fatalf("ListProjectItems: %v", err)
	}
	if gotPath != "/projects/018f-a/items/" {
		t.Errorf("path = %s, want /projects/018f-a/items/", gotPath)
	}
	if gotQuery != "archived=true" {
		t.Errorf("query = %q, want archived=true", gotQuery)
	}
	if len(items) != 1 || items[0].Title != "First" {
		t.Errorf("items = %+v", items)
	}

	// Without archived, no query string should be sent.
	_, _ = client.ListProjectItems(context.Background(), "018f-a", false)
	if gotQuery != "" {
		t.Errorf("query = %q, want empty when archived=false", gotQuery)
	}
}
