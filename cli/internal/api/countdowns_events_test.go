package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCreateCountdown_SendsDateString(t *testing.T) {
	var gotPath string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"name":"Lease","notes":null,"due_date":"2027-03-01"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	cd, err := client.CreateCountdown(context.Background(), CountdownCreateInput{Name: "Lease", DueDate: "2027-03-01"})
	if err != nil {
		t.Fatalf("CreateCountdown: %v", err)
	}
	if gotPath != "/countdowns/" {
		t.Errorf("path = %s", gotPath)
	}
	if gotBody["due_date"] != "2027-03-01" {
		t.Errorf("due_date = %v", gotBody["due_date"])
	}
	if cd.DueDate != "2027-03-01" {
		t.Errorf("cd.DueDate = %q (date-only field decoded as string)", cd.DueDate)
	}
}

func TestUpdateCountdown_PatchPartial(t *testing.T) {
	var gotMethod string
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":1,"name":"Lease","notes":null,"due_date":"2027-04-01"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	due := "2027-04-01"
	if _, err := client.UpdateCountdown(context.Background(), 1, CountdownUpdateInput{DueDate: &due}); err != nil {
		t.Fatalf("UpdateCountdown: %v", err)
	}
	if gotMethod != http.MethodPatch {
		t.Errorf("method = %s, want PATCH", gotMethod)
	}
	if len(gotBody) != 1 || gotBody["due_date"] != "2027-04-01" {
		t.Errorf("partial body = %v", gotBody)
	}
}

func TestCreateEvent_SendsRequiredFields(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":7,"name":"Show","date":"2026-09-01T20:00:00Z","venue":"Hall","url":null,"cost":45,"attending":true,"notes":null}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	event, err := client.CreateEvent(context.Background(), EventCreateInput{Name: "Show", Date: "2026-09-01 20:00", Venue: "Hall", Cost: 45, Attending: true})
	if err != nil {
		t.Fatalf("CreateEvent: %v", err)
	}
	// cost and attending are required by the API, so they must always be sent.
	if gotBody["cost"] != float64(45) || gotBody["attending"] != true {
		t.Errorf("body = %v", gotBody)
	}
	if gotBody["date"] != "2026-09-01 20:00" {
		t.Errorf("date should be sent as the raw string for server-side parsing, got %v", gotBody["date"])
	}
	if !event.Attending || event.Date.IsZero() {
		t.Errorf("event = %+v", event)
	}
}

func TestAttendEvent_PatchPath(t *testing.T) {
	var gotMethod string
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":7,"name":"Show","date":"2026-09-01T20:00:00Z","venue":"Hall","url":null,"cost":45,"attending":true,"notes":null}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	event, err := client.AttendEvent(context.Background(), 7)
	if err != nil {
		t.Fatalf("AttendEvent: %v", err)
	}
	if gotMethod != http.MethodPatch || gotPath != "/events/7/attend/" {
		t.Errorf("%s %s, want PATCH /events/7/attend/", gotMethod, gotPath)
	}
	if !event.Attending {
		t.Error("event should be attending")
	}
}
