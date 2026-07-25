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

func TestListProjects_DecodesAndAuthenticates(t *testing.T) {
	var gotAuth string
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[
			{"id":"018f-a","name":"Personal OS","description":"the roadmap","position":0,"created_at":"2026-07-24T00:00:00Z","item_count":3},
			{"id":"018f-b","name":"House","description":null,"position":1,"created_at":"2026-07-24T00:00:00Z","item_count":0}
		]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("abc123"))
	projects, err := client.ListProjects(context.Background())
	if err != nil {
		t.Fatalf("ListProjects: %v", err)
	}

	if gotAuth != "Bearer abc123" {
		t.Errorf("Authorization header = %q, want %q", gotAuth, "Bearer abc123")
	}
	if gotPath != "/projects/" {
		t.Errorf("request path = %q, want /projects/", gotPath)
	}
	if len(projects) != 2 {
		t.Fatalf("got %d projects, want 2", len(projects))
	}
	if projects[0].Name != "Personal OS" || projects[0].ItemCount == nil || *projects[0].ItemCount != 3 {
		t.Errorf("project[0] = %+v", projects[0])
	}
	if projects[1].Description != nil {
		t.Errorf("project[1] description should be nil, got %v", projects[1].Description)
	}
}

func TestGetProject_NotFoundIsAPIError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		_, _ = w.Write([]byte(`{"detail":"project 018f-x not found"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.GetProject(context.Background(), "018f-x")

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if !apiErr.NotFound() {
		t.Errorf("StatusCode = %d, want 404", apiErr.StatusCode)
	}
	if apiErr.Message != "project 018f-x not found" {
		t.Errorf("Message = %q", apiErr.Message)
	}
}

func TestGetProject_UnauthorizedFlagged(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.GetProject(context.Background(), "x")

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
	_, err := client.ListProjects(context.Background())

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

// FastAPI request-validation errors (422) return a detail *array*; the client
// must summarize it into a readable message rather than dropping it.
func TestDecodeAPIError_ValidationArray(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnprocessableEntity)
		_, _ = w.Write([]byte(`{"detail":[{"type":"missing","loc":["body","name"],"msg":"Field required"}]}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.CreateProject(context.Background(), ProjectCreateInput{})

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if apiErr.Message != "name: Field required" {
		t.Errorf("Message = %q, want %q", apiErr.Message, "name: Field required")
	}
}

// The 500 handler returns {"message": ...} with no detail; the client must fall
// back to that field.
func TestDecodeAPIError_MessageFallback(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_, _ = w.Write([]byte(`{"message":"Internal server error: ValueError"}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	_, err := client.ListProjects(context.Background())

	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *APIError, got %v", err)
	}
	if apiErr.Message != "Internal server error: ValueError" {
		t.Errorf("Message = %q", apiErr.Message)
	}
}
