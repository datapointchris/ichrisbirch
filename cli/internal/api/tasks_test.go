package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListTasks_LimitQueryParam(t *testing.T) {
	var gotPath string
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":1,"name":"A","notes":null,"category":"chore","priority":1,"add_date":"2026-07-24T00:00:00Z","complete_date":null}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))

	limit := 5
	tasks, err := client.ListTasks(context.Background(), &limit, "", DateBounds{})
	if err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if gotPath != "/tasks/" || gotQuery != "limit=5" {
		t.Errorf("path=%q query=%q, want /tasks/ limit=5", gotPath, gotQuery)
	}
	if len(tasks) != 1 || tasks[0].Completed() {
		t.Errorf("tasks = %+v", tasks)
	}

	// nil limit omits the query string entirely.
	_, _ = client.ListTasks(context.Background(), nil, "", DateBounds{})
	if gotQuery != "" {
		t.Errorf("query = %q, want empty for nil limit", gotQuery)
	}
}

func TestCompleteTask_PatchPath(t *testing.T) {
	var gotMethod string
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":42,"name":"A","notes":null,"category":"chore","priority":1,"add_date":"2026-07-24T00:00:00Z","complete_date":"2026-07-24T10:00:00Z"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	task, err := client.CompleteTask(context.Background(), 42)
	if err != nil {
		t.Fatalf("CompleteTask: %v", err)
	}
	if gotMethod != http.MethodPatch || gotPath != "/tasks/42/complete/" {
		t.Errorf("%s %s, want PATCH /tasks/42/complete/", gotMethod, gotPath)
	}
	if !task.Completed() {
		t.Error("task should be completed (complete_date set)")
	}
}

func TestShiftTask_NegativePositionsInPath(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":42,"name":"A","notes":null,"category":"chore","priority":1,"add_date":"2026-07-24T00:00:00Z","complete_date":null}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.ShiftTask(context.Background(), 42, -2); err != nil {
		t.Fatalf("ShiftTask: %v", err)
	}
	if gotPath != "/tasks/42/shift/-2/" {
		t.Errorf("path = %s, want /tasks/42/shift/-2/", gotPath)
	}
}

func TestCreateTask_OmitsUnsetPriority(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"name":"A","notes":null,"category":"chore","priority":1,"add_date":"2026-07-24T00:00:00Z","complete_date":null}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	if _, err := client.CreateTask(context.Background(), TaskCreateInput{Name: "A", Category: "chore"}); err != nil {
		t.Fatalf("CreateTask: %v", err)
	}
	if gotBody["name"] != "A" || gotBody["category"] != "chore" {
		t.Errorf("body = %v", gotBody)
	}
	if _, ok := gotBody["priority"]; ok {
		t.Errorf("priority should be omitted when unset, body = %v", gotBody)
	}
}

func TestReorderTasks_ReturnsMessage(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/tasks/reorder/" || r.Method != http.MethodPost {
			t.Errorf("unexpected %s %s", r.Method, r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"message":"Reordered 7 tasks"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	msg, err := client.ReorderTasks(context.Background())
	if err != nil {
		t.Fatalf("ReorderTasks: %v", err)
	}
	if msg != "Reordered 7 tasks" {
		t.Errorf("msg = %q", msg)
	}
}

// The common call must send no status at all rather than status=open — an
// explicit default in every URL makes the server's default unchangeable.
func TestListTasks_OmitsTheStatusParamByDefault(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, "", DateBounds{}); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want no parameters at all", *query)
	}
}

func TestListTasks_SendsTheStatus(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, TaskStatusCompleted, DateBounds{}); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "status=completed" {
		t.Errorf("query = %q, want status=completed", *query)
	}
}

func TestListTasks_CarriesTheDateBounds(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	bounds := DateBounds{Start: "2026-08-17", End: "2026-08-23"}
	if _, err := client.ListTasks(context.Background(), nil, TaskStatusCompleted, bounds); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "end_date=2026-08-23&start_date=2026-08-17&status=completed" {
		t.Errorf("query = %q, want both bounds beside the status", *query)
	}
}

func TestListTasks_OneBoundNarrowsOnItsOwn(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, "", DateBounds{End: "2026-08-23"}); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "end_date=2026-08-23" {
		t.Errorf("query = %q, want the end bound alone", *query)
	}
}

func TestListTasks_CarriesBothLimitAndStatus(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	limit := 5
	if _, err := client.ListTasks(context.Background(), &limit, TaskStatusAll, DateBounds{}); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "limit=5&status=all" {
		t.Errorf("query = %q, want limit=5&status=all", *query)
	}
}
