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
		_, _ = w.Write([]byte(`[` + openTaskJSON + `]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))

	limit := 5
	tasks, err := client.ListTasks(context.Background(), &limit, "", "", "", "", "")
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
	_, _ = client.ListTasks(context.Background(), nil, "", "", "", "", "")
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
		_, _ = w.Write([]byte(`{"id":42,"name":"A","notes":null,"category":"Chore","rank_at":"2026-08-23T00:00:00Z","window_days":30,"pinned":false,"autotask_id":null,"add_date":"2026-07-24T00:00:00Z","complete_date":"2026-07-24T10:00:00Z","drop_date":null,"drop_reason":null}`))
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

const openTaskJSON = `{"id":42,"name":"A","notes":null,"category":"Chore","rank_at":"2026-08-23T00:00:00Z","window_days":30,"pinned":false,"autotask_id":null,"add_date":"2026-07-24T00:00:00Z","complete_date":null,"drop_date":null,"drop_reason":null}`

// recordRequest serves openTaskJSON and records the method, path and decoded body.
func recordRequest(t *testing.T, response string) (*Client, *string, *string, *map[string]any) {
	t.Helper()
	var method, path string
	var body map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		method, path = r.Method, r.URL.Path
		body = nil
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &body)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(response))
	}))
	t.Cleanup(srv.Close)
	return New(srv.URL, staticTokenClient("t")), &method, &path, &body
}

func TestTask_DecodesTheRankingFields(t *testing.T) {
	var task Task
	raw := `{"id":7,"name":"Trim nails","notes":null,"category":"Dingo","rank_at":"2026-10-14T12:00:00Z","window_days":7,"pinned":true,"autotask_id":3,"add_date":"2026-10-07T12:00:00Z","complete_date":null,"drop_date":"2026-10-08T12:00:00Z","drop_reason":"done by the groomer"}`
	if err := json.Unmarshal([]byte(raw), &task); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if task.WindowDays != 7 || !task.Pinned || task.AutoTaskID == nil || *task.AutoTaskID != 3 {
		t.Errorf("task = %+v", task)
	}
	if !task.Dropped() || task.Completed() || *task.DropReason != "done by the groomer" {
		t.Errorf("closed state = completed %v dropped %v", task.Completed(), task.Dropped())
	}
}

func TestSnoozeTask_PatchesTheSnoozePath(t *testing.T) {
	client, method, path, _ := recordRequest(t, openTaskJSON)
	if _, err := client.SnoozeTask(context.Background(), 42); err != nil {
		t.Fatalf("SnoozeTask: %v", err)
	}
	if *method != http.MethodPatch || *path != "/tasks/42/snooze/" {
		t.Errorf("%s %s, want PATCH /tasks/42/snooze/", *method, *path)
	}
}

func TestDropTask_SendsTheReason(t *testing.T) {
	client, method, path, body := recordRequest(t, openTaskJSON)
	if _, err := client.DropTask(context.Background(), 42, "lost interest"); err != nil {
		t.Fatalf("DropTask: %v", err)
	}
	if *method != http.MethodPatch || *path != "/tasks/42/drop/" {
		t.Errorf("%s %s, want PATCH /tasks/42/drop/", *method, *path)
	}
	if (*body)["reason"] != "lost interest" {
		t.Errorf("body = %v, want the reason", *body)
	}
}

func TestDropTask_OmitsAnEmptyReason(t *testing.T) {
	client, _, _, body := recordRequest(t, openTaskJSON)
	if _, err := client.DropTask(context.Background(), 42, ""); err != nil {
		t.Fatalf("DropTask: %v", err)
	}
	if _, ok := (*body)["reason"]; ok {
		t.Errorf("body = %v, want no reason key", *body)
	}
}

func TestSetTaskPinned_SendsFalseRatherThanOmittingIt(t *testing.T) {
	client, method, path, body := recordRequest(t, openTaskJSON)
	if _, err := client.SetTaskPinned(context.Background(), 42, false); err != nil {
		t.Fatalf("SetTaskPinned: %v", err)
	}
	if *method != http.MethodPatch || *path != "/tasks/42/" {
		t.Errorf("%s %s, want PATCH /tasks/42/", *method, *path)
	}
	if pinned, ok := (*body)["pinned"]; !ok || pinned != false {
		t.Errorf("body = %v, want pinned=false sent", *body)
	}
}

func TestCreateTask_OmitsAnUnsetWindow(t *testing.T) {
	client, _, _, body := recordRequest(t, openTaskJSON)
	if _, err := client.CreateTask(context.Background(), TaskCreateInput{Name: "A", Category: "Chore"}); err != nil {
		t.Fatalf("CreateTask: %v", err)
	}
	if (*body)["name"] != "A" || (*body)["category"] != "Chore" {
		t.Errorf("body = %v", *body)
	}
	if _, ok := (*body)["window_days"]; ok {
		t.Errorf("window_days should be omitted when unset so the category's applies, body = %v", *body)
	}
}

func TestListTaskCategories_DecodesWindows(t *testing.T) {
	client, _, path, _ := recordRequest(t, `[{"name":"Dingo","window_days":7}]`)
	categories, err := client.ListTaskCategories(context.Background())
	if err != nil {
		t.Fatalf("ListTaskCategories: %v", err)
	}
	if *path != "/tasks/categories/" || len(categories) != 1 || categories[0].WindowDays != 7 {
		t.Errorf("path %s categories %+v", *path, categories)
	}
}

func TestUpdateTaskCategory_PatchesTheWindow(t *testing.T) {
	client, method, path, body := recordRequest(t, `{"name":"Home","window_days":12}`)
	if _, err := client.UpdateTaskCategory(context.Background(), "Home", 12); err != nil {
		t.Fatalf("UpdateTaskCategory: %v", err)
	}
	if *method != http.MethodPatch || *path != "/tasks/categories/Home/" {
		t.Errorf("%s %s, want PATCH /tasks/categories/Home/", *method, *path)
	}
	if (*body)["window_days"] != float64(12) {
		t.Errorf("body = %v", *body)
	}
}

// The common call must send no status at all rather than status=open — an
// explicit default in every URL makes the server's default unchangeable.
func TestListTasks_OmitsTheStatusParamByDefault(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, "", "", "", "", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want no parameters at all", *query)
	}
}

func TestListTasks_SendsTheStatus(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, TaskStatusCompleted, "", "", "", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "status=completed" {
		t.Errorf("query = %q, want status=completed", *query)
	}
}

func TestListTasks_CarriesTheCompletionBounds(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, TaskStatusCompleted, "", "2026-08-17", "2026-08-23", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "end_date=2026-08-23&start_date=2026-08-17&status=completed" {
		t.Errorf("query = %q, want both bounds beside the status", *query)
	}
}

func TestListTasks_NamesTheZoneABareDayIsReadIn(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, TaskStatusCompleted, "", "2026-08-20", "2026-08-20", "America/New_York"); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "end_date=2026-08-20&start_date=2026-08-20&status=completed&timezone=America%2FNew_York" {
		t.Errorf("query = %q, want the zone beside the bounds", *query)
	}
}

func TestListTasks_AZoneWithNoBoundIsNotSent(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, "", "", "", "", "America/New_York"); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want nothing: a zone narrows nothing on its own", *query)
	}
}

func TestListTasks_OneBoundNarrowsOnItsOwn(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, "", "", "", "2026-08-23", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "end_date=2026-08-23" {
		t.Errorf("query = %q, want the end bound alone", *query)
	}
}

func TestListTasks_CarriesBothLimitAndStatus(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	limit := 5
	if _, err := client.ListTasks(context.Background(), &limit, TaskStatusAll, "", "", "", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "limit=5&status=all" {
		t.Errorf("query = %q, want limit=5&status=all", *query)
	}
}

func TestListTasks_SendsTheCategory(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, "", "Personal", "", "", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "category=Personal" {
		t.Errorf("query = %q, want category=Personal", *query)
	}
}

// Sent rather than filtered here, so the limit caps the category asked for
// instead of the first N of every category.
func TestListTasks_CarriesTheCategoryBesideTheLimit(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	limit := 3
	if _, err := client.ListTasks(context.Background(), &limit, "", "Personal", "", "", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "category=Personal&limit=3" {
		t.Errorf("query = %q, want both", *query)
	}
}

func TestListTasks_OmitsTheCategoryParamWhenEmpty(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListTasks(context.Background(), nil, TaskStatusAll, "", "", "", ""); err != nil {
		t.Fatalf("ListTasks: %v", err)
	}
	if *query != "status=all" {
		t.Errorf("query = %q, want the status alone", *query)
	}
}
