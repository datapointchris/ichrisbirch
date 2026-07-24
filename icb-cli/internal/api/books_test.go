package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestListBooks_OwnershipFilter(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[{"id":1,"isbn":null,"title":"DDIA","author":"Kleppmann","tags":["db"],"ownership":"owned","progress":"unread","priority":null,"rating":null}]`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	books, err := client.ListBooks(context.Background(), "owned")
	if err != nil {
		t.Fatalf("ListBooks: %v", err)
	}
	if gotQuery != "ownership=owned" {
		t.Errorf("query = %q", gotQuery)
	}
	if len(books) != 1 || books[0].Tags[0] != "db" {
		t.Errorf("books = %+v", books)
	}

	_, _ = client.ListBooks(context.Background(), "")
	if gotQuery != "" {
		t.Errorf("query = %q, want empty for no ownership", gotQuery)
	}
}

func TestCreateBook_SendsTagsAndOmitsUnset(t *testing.T) {
	var gotBody map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, _ := io.ReadAll(r.Body)
		_ = json.Unmarshal(raw, &gotBody)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"id":1,"isbn":null,"title":"DDIA","author":"Kleppmann","tags":["db","systems"],"ownership":"owned","progress":"unread","priority":null,"rating":null}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	rating := 5
	book, err := client.CreateBook(context.Background(), BookCreateInput{
		Title: "DDIA", Author: "Kleppmann", Tags: []string{"db", "systems"}, Rating: &rating,
	})
	if err != nil {
		t.Fatalf("CreateBook: %v", err)
	}
	tags, ok := gotBody["tags"].([]any)
	if !ok || len(tags) != 2 {
		t.Errorf("tags = %v", gotBody["tags"])
	}
	if gotBody["rating"] != float64(5) {
		t.Errorf("rating = %v", gotBody["rating"])
	}
	// Unset optional fields must be omitted, not sent as nulls/zeros.
	for _, k := range []string{"isbn", "purchase_price", "priority", "location"} {
		if _, present := gotBody[k]; present {
			t.Errorf("%s should be omitted when unset, body = %v", k, gotBody)
		}
	}
	if book.Title != "DDIA" {
		t.Errorf("book = %+v", book)
	}
}

func TestGetBookByISBN_Path(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"id":1,"isbn":"9781449373320","title":"DDIA","author":"Kleppmann","tags":["db"],"ownership":"owned","progress":"unread","priority":null,"rating":null}`))
	}))
	defer srv.Close()

	client := New(srv.URL, staticTokenClient("t"))
	book, err := client.GetBookByISBN(context.Background(), "9781449373320")
	if err != nil {
		t.Fatalf("GetBookByISBN: %v", err)
	}
	if gotPath != "/books/isbn/9781449373320/" {
		t.Errorf("path = %s", gotPath)
	}
	if book.ISBN == nil || *book.ISBN != "9781449373320" {
		t.Errorf("book.ISBN = %v", book.ISBN)
	}
}
