package api

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
)

// staticTokenClient mimics the oauth2 client the CLI injects: an http.Client
// whose transport stamps a fixed bearer token on every request, so tests can
// assert the client forwards Authorization without a real token source.
func staticTokenClient(token string) *http.Client {
	return &http.Client{Transport: bearerTransport{token: token}}
}

type bearerTransport struct{ token string }

func (b bearerTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	req.Header.Set("Authorization", "Bearer "+b.token)
	return http.DefaultTransport.RoundTrip(req)
}

func TestListTasks_DecodesAndAuthenticates(t *testing.T) {
	var gotAuth string
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":7,"name":"Renew registration","notes":null,"category":"Chore","window_days":14}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("abc123"))
	tasks, err := client.ListTasks(context.Background(), nil, "", "", Window{})
	if err != nil {
		t.Fatalf("ListTasks: %v", err)
	}

	if gotAuth != "Bearer abc123" {
		t.Errorf("Authorization header = %q, want %q", gotAuth, "Bearer abc123")
	}
	if gotPath != "/api/v1/tasks" {
		t.Errorf("request path = %q, want /api/v1/tasks", gotPath)
	}
	if len(tasks) != 1 || tasks[0].Name != "Renew registration" || tasks[0].Notes != nil {
		t.Errorf("tasks = %+v", tasks)
	}
}

func TestGetTask_NotFoundIsAPIError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		_, _ = w.Write([]byte(`{"error":"Not Found","message":"task 999 not found"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.GetTask(context.Background(), 999)

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if !apiErr.NotFound() {
		t.Errorf("StatusCode = %d, want 404", apiErr.StatusCode)
	}
	if apiErr.Message != "task 999 not found" {
		t.Errorf("Message = %q", apiErr.Message)
	}
}

func TestGetTask_UnauthorizedFlagged(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.GetTask(context.Background(), 1)

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if !apiErr.Unauthorized() {
		t.Error("expected Unauthorized() true for 401")
	}
}

// A non-JSON error body (proxy page, Authelia redirect) must still yield a
// usable status-only APIError rather than a decode failure.
func TestSend_NonJSONErrorBody(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusBadGateway)
		_, _ = w.Write([]byte("<html>502 Bad Gateway</html>"))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.ListTasks(context.Background(), nil, "", "", Window{})

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if apiErr.StatusCode != http.StatusBadGateway {
		t.Errorf("StatusCode = %d, want 502", apiErr.StatusCode)
	}
	if apiErr.Message != "" {
		t.Errorf("Message = %q, want empty for non-JSON body", apiErr.Message)
	}
}
