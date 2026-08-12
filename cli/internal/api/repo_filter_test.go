package api

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

// recordQuery serves an empty JSON list and captures the raw query string, which
// is what these tests are actually about: an absent filter and an empty one have
// to reach the server as different requests.
func recordQuery(t *testing.T, body string) (*Client, *string) {
	t.Helper()
	var got string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(body))
	}))
	t.Cleanup(srv.Close)
	return New(srv.URL, staticTokenClient("t")), &got
}

func strptr(s string) *string { return &s }

func TestListItems_OmitsTheRepoParamWhenUnfiltered(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListItems(context.Background(), nil, ""); err != nil {
		t.Fatalf("ListItems: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want no parameters at all", *query)
	}
}

func TestListItems_SendsTheRepoParam(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListItems(context.Background(), strptr("dotfiles"), ""); err != nil {
		t.Fatalf("ListItems: %v", err)
	}
	if *query != "repo=dotfiles" {
		t.Errorf("query = %q, want repo=dotfiles", *query)
	}
}

// The untagged items are a real question — errands and home projects — and an
// empty repo is how it is asked. Dropping the empty value would silently turn it
// into "everything".
func TestListItems_SendsAnEmptyRepoForUntaggedWork(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListItems(context.Background(), strptr(""), ""); err != nil {
		t.Fatalf("ListItems: %v", err)
	}
	if *query != "repo=" {
		t.Errorf("query = %q, want repo= (present but empty)", *query)
	}
}

func TestSearchItems_KeepsBothTheQueryAndTheRepo(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.SearchItems(context.Background(), "sync", strptr("todoui")); err != nil {
		t.Fatalf("SearchItems: %v", err)
	}
	if *query != "q=sync&repo=todoui" {
		t.Errorf("query = %q, want both parameters", *query)
	}
}

func TestListBlockedItems_SendsTheRepoParam(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListBlockedItems(context.Background(), strptr("homelab")); err != nil {
		t.Fatalf("ListBlockedItems: %v", err)
	}
	if *query != "repo=homelab" {
		t.Errorf("query = %q, want repo=homelab", *query)
	}
}

func TestListProjects_SendsTheRepoParam(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListProjects(context.Background(), strptr("indy"), ""); err != nil {
		t.Fatalf("ListProjects: %v", err)
	}
	if *query != "repo=indy" {
		t.Errorf("query = %q, want repo=indy", *query)
	}
}

func TestListProjects_DecodesTheDerivedRepos(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[
			{"id":"018f-a","name":"Spans three","description":null,"kind":"build","position":0,"created_at":"2026-07-24T00:00:00Z","item_count":3,"open_count":3,"completed_count":0,"repos":["icb","ichrisbirch","todoui"]}
		]`))
	}))
	defer srv.Close()

	projects, err := New(srv.URL, staticTokenClient("t")).ListProjects(context.Background(), nil, "")
	if err != nil {
		t.Fatalf("ListProjects: %v", err)
	}
	if len(projects[0].Repos) != 3 || projects[0].Repos[0] != "icb" {
		t.Errorf("repos = %v, want all three in order", projects[0].Repos)
	}
}

func TestListItems_OmitsTheStatusParamByDefault(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListItems(context.Background(), nil, ""); err != nil {
		t.Fatalf("ListItems: %v", err)
	}
	if *query != "" {
		t.Errorf("query = %q, want no parameters at all", *query)
	}
}

func TestListItems_CarriesBothTheRepoAndTheStatus(t *testing.T) {
	client, query := recordQuery(t, `[]`)
	if _, err := client.ListItems(context.Background(), strptr("dotfiles"), ItemStatusAll); err != nil {
		t.Fatalf("ListItems: %v", err)
	}
	if *query != "repo=dotfiles&status=all" {
		t.Errorf("query = %q, want repo=dotfiles&status=all", *query)
	}
}
