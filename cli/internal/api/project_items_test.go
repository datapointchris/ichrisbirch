package api

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCreateItem_SendsProjectIDs(t *testing.T) {
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":"item-1","title":"Ship it","notes":null,"completed":false,"archived":false,"created_at":"2026-07-24T00:00:00Z","updated_at":"2026-07-24T00:00:00Z","projects":[{"id":"p1","name":"P","description":null,"position":0,"created_at":"2026-07-24T00:00:00Z"}],"dependency_ids":[]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	detail, err := client.CreateItem(context.Background(), ProjectItemCreateInput{Title: "Ship it", ProjectIDs: []string{"p1", "p2"}})
	if err != nil {
		t.Fatalf("CreateItem: %v", err)
	}
	if gotPath != "/project-items/" {
		t.Errorf("path = %s, want /project-items/", gotPath)
	}
	ids, ok := gotBody["project_ids"].([]any)
	if !ok || len(ids) != 2 || ids[0] != "p1" {
		t.Errorf("project_ids = %v", gotBody["project_ids"])
	}
	if len(detail.Projects) != 1 || detail.Projects[0].Name != "P" {
		t.Errorf("detail.Projects = %+v", detail.Projects)
	}
}

func TestUpdateItem_PatchOnlyChangedFields(t *testing.T) {
	var gotMethod string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":"item-1","title":"t","notes":null,"completed":true,"archived":false,"created_at":"2026-07-24T00:00:00Z","updated_at":"2026-07-24T00:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	done := true
	_, err := client.UpdateItem(context.Background(), "item-1", ProjectItemUpdateInput{Completed: &done})
	if err != nil {
		t.Fatalf("UpdateItem: %v", err)
	}
	if gotMethod != http.MethodPatch {
		t.Errorf("method = %s, want PATCH", gotMethod)
	}
	if len(gotBody) != 1 || gotBody["completed"] != true {
		t.Errorf("partial update body = %v, want only {completed:true}", gotBody)
	}
}

func TestReorderItem_PathAndBody(t *testing.T) {
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":"item-1","title":"t","notes":null,"completed":false,"archived":false,"created_at":"2026-07-24T00:00:00Z","updated_at":"2026-07-24T00:00:00Z","position":3}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	item, err := client.ReorderItem(context.Background(), "item-1", ProjectItemReorderInput{ProjectID: "p1", Position: 3})
	if err != nil {
		t.Fatalf("ReorderItem: %v", err)
	}
	if gotPath != "/project-items/item-1/reorder/" {
		t.Errorf("path = %s", gotPath)
	}
	if gotBody["project_id"] != "p1" || gotBody["position"] != float64(3) {
		t.Errorf("body = %v", gotBody)
	}
	if item.Position != 3 {
		t.Errorf("item.Position = %d, want 3", item.Position)
	}
}

func TestRemoveItemFromProject_LastProjectConflict(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusConflict)
		_, _ = w.Write([]byte(`{"detail":"Cannot remove item from its last project. Delete the item instead."}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	err := client.RemoveItemFromProject(context.Background(), "item-1", "p1")

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if apiErr.StatusCode != http.StatusConflict {
		t.Errorf("StatusCode = %d, want 409", apiErr.StatusCode)
	}
	if apiErr.Message == "" {
		t.Error("expected the 409 message to be surfaced")
	}
}

func TestItemTasks_ListCreateUpdateDelete(t *testing.T) {
	var lastMethod string
	var lastPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		lastMethod = r.Method
		lastPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		switch r.Method {
		case http.MethodDelete:
			w.WriteHeader(http.StatusNoContent)
		default:
			_, _ = w.Write([]byte(`{"id":"task-1","item_id":"item-1","title":"t","completed":false,"position":0,"created_at":"2026-07-24T00:00:00Z"}`))
		}
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	ctx := context.Background()

	if _, err := client.CreateItemTask(ctx, "item-1", ProjectItemTaskCreateInput{Title: "t"}); err != nil {
		t.Fatalf("CreateItemTask: %v", err)
	}
	if lastPath != "/project-items/item-1/tasks/" || lastMethod != http.MethodPost {
		t.Errorf("create: %s %s", lastMethod, lastPath)
	}

	done := true
	if _, err := client.UpdateItemTask(ctx, "item-1", "task-1", ProjectItemTaskUpdateInput{Completed: &done}); err != nil {
		t.Fatalf("UpdateItemTask: %v", err)
	}
	if lastPath != "/project-items/item-1/tasks/task-1/" || lastMethod != http.MethodPatch {
		t.Errorf("update: %s %s", lastMethod, lastPath)
	}

	if err := client.DeleteItemTask(ctx, "item-1", "task-1"); err != nil {
		t.Fatalf("DeleteItemTask: %v", err)
	}
	if lastPath != "/project-items/item-1/tasks/task-1/" || lastMethod != http.MethodDelete {
		t.Errorf("delete: %s %s", lastMethod, lastPath)
	}
}
