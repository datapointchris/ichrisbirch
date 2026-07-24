package api

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListAutoTasks_DecodesRows(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":2,"name":"Clean kitchen","category":"Chore","priority":22,"notes":null,"frequency":"Daily","max_concurrent":2,"first_run_date":"2026-07-24T14:33:26Z","last_run_date":"2026-07-24T14:33:26Z","run_count":0}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	autotasks, err := client.ListAutoTasks(context.Background())
	if err != nil {
		t.Fatalf("ListAutoTasks: %v", err)
	}
	if gotPath != "/autotasks/" {
		t.Errorf("path = %s", gotPath)
	}
	if len(autotasks) != 1 {
		t.Fatalf("autotasks = %+v", autotasks)
	}
	a := autotasks[0]
	if a.ID != 2 || a.Name != "Clean kitchen" || a.Frequency != "Daily" || a.MaxConcurrent != 2 {
		t.Errorf("autotask = %+v", a)
	}
	if a.Notes != nil {
		t.Errorf("notes = %v, want nil", a.Notes)
	}
	if a.FirstRunDate.IsZero() || a.LastRunDate.IsZero() {
		t.Errorf("dates not decoded: %+v", a)
	}
}

func TestGetAutoTask_ByID(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":7,"name":"Water plants","category":"Chore","priority":10,"notes":"balcony only","frequency":"Weekly","max_concurrent":1,"first_run_date":"2026-07-24T00:00:00Z","last_run_date":"2026-07-24T00:00:00Z","run_count":3}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	autotask, err := client.GetAutoTask(context.Background(), 7)
	if err != nil {
		t.Fatalf("GetAutoTask: %v", err)
	}
	if gotPath != "/autotasks/7/" {
		t.Errorf("path = %s", gotPath)
	}
	if autotask.RunCount != 3 || autotask.Notes == nil || *autotask.Notes != "balcony only" {
		t.Errorf("autotask = %+v", autotask)
	}
}
