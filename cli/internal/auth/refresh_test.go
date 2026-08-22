package auth

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"golang.org/x/oauth2"

	"github.com/datapointchris/ichrisbirch/cli/internal/config"
)

// rotatingIDP is Authelia's refresh behavior: every refresh consumes the token
// presented and issues a new one, and presenting a consumed token revokes the
// whole grant rather than merely failing. That last part is what turns a race
// between two icb processes into a re-login.
type rotatingIDP struct {
	server *httptest.Server

	mu        sync.Mutex
	current   string
	consumed  map[string]bool
	revoked   bool
	refreshes int
	replays   int
}

func newRotatingIDP(t *testing.T, initialRefreshToken string) *rotatingIDP {
	t.Helper()
	idp := &rotatingIDP{current: initialRefreshToken, consumed: map[string]bool{}}
	mux := http.NewServeMux()
	mux.HandleFunc("/.well-known/openid-configuration", func(w http.ResponseWriter, _ *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]string{
			"issuer":                        idp.server.URL,
			"token_endpoint":                idp.server.URL + "/token",
			"device_authorization_endpoint": idp.server.URL + "/device",
		})
	})
	mux.HandleFunc("/token", idp.token)
	idp.server = httptest.NewServer(mux)
	t.Cleanup(idp.server.Close)
	return idp
}

func (r *rotatingIDP) token(w http.ResponseWriter, req *http.Request) {
	_ = req.ParseForm()
	presented := req.FormValue("refresh_token")

	r.mu.Lock()
	defer r.mu.Unlock()

	switch {
	case r.revoked:
		r.deny(w)
		return
	case r.consumed[presented]:
		// Reuse detection: the grant dies, taking the token the winner is
		// holding with it.
		r.replays++
		r.revoked = true
		r.deny(w)
		return
	case presented != r.current:
		r.deny(w)
		return
	}

	r.refreshes++
	r.consumed[presented] = true
	r.current = fmt.Sprintf("rt-%d", r.refreshes)

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"access_token":  fmt.Sprintf("at-%d", r.refreshes),
		"refresh_token": r.current,
		"token_type":    "bearer",
		"expires_in":    3600,
	})
}

func (r *rotatingIDP) deny(w http.ResponseWriter) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	_ = json.NewEncoder(w).Encode(map[string]any{"error": "invalid_grant"})
}

func (r *rotatingIDP) counts() (refreshes, replays int, revoked bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.refreshes, r.replays, r.revoked
}

// seedExpiredToken puts an expired access token and a live refresh token in the
// store, which is the state every icb process starts from once an hour has
// passed since the last call.
func seedExpiredToken(t *testing.T, store *TokenStore, clientID, refreshToken string) {
	t.Helper()
	err := store.Save(clientID, &oauth2.Token{
		AccessToken:  "at-initial",
		RefreshToken: refreshToken,
		TokenType:    "bearer",
		Expiry:       time.Now().Add(-time.Hour),
	})
	if err != nil {
		t.Fatalf("seed the store: %v", err)
	}
}

// Several icb processes starting at once is the ordinary case, not an edge one:
// doit resolves each pursuit's evidence in its own process. Exactly one of them
// may refresh, because the second refresh is a replay that revokes the grant.
func TestTokenSource_ConcurrentProcessesRefreshOnce(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", t.TempDir())
	idp := newRotatingIDP(t, "rt-initial")
	cfg := config.Config{Issuer: idp.server.URL, ClientID: "icb-cli-archlinux"}
	store := &TokenStore{backend: newFakeKeyring()}
	seedExpiredToken(t, store, cfg.ClientID, "rt-initial")

	const processes = 8
	var wg sync.WaitGroup
	errs := make([]error, processes)
	tokens := make([]string, processes)
	for i := range processes {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// Each goroutine builds its own token source from the shared store,
			// which is what a separate process does.
			source, err := TokenSource(context.Background(), cfg, store)
			if err != nil {
				errs[i] = err
				return
			}
			tok, err := source.Token()
			if err != nil {
				errs[i] = err
				return
			}
			tokens[i] = tok.AccessToken
		}()
	}
	wg.Wait()

	for i, err := range errs {
		if err != nil {
			t.Errorf("process %d failed: %v", i, err)
		}
	}
	refreshes, replays, revoked := idp.counts()
	if refreshes != 1 {
		t.Errorf("refreshes = %d, want exactly 1 across %d processes", refreshes, processes)
	}
	if replays != 0 {
		t.Errorf("replays = %d, want 0 — a replay is what revokes the grant", replays)
	}
	if revoked {
		t.Error("the grant was revoked, which costs the user an interactive login")
	}
	for i, at := range tokens {
		if at != "at-1" {
			t.Errorf("process %d used access token %q, want the single refreshed one", i, at)
		}
	}
}

// The refreshed token has to reach the keychain, or the next process starts from
// the token this one just consumed and replays it.
func TestTokenSource_PersistsTheRefreshedToken(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", t.TempDir())
	idp := newRotatingIDP(t, "rt-initial")
	cfg := config.Config{Issuer: idp.server.URL, ClientID: "icb-cli-archlinux"}
	store := &TokenStore{backend: newFakeKeyring()}
	seedExpiredToken(t, store, cfg.ClientID, "rt-initial")

	source, err := TokenSource(context.Background(), cfg, store)
	if err != nil {
		t.Fatalf("TokenSource: %v", err)
	}
	if _, err := source.Token(); err != nil {
		t.Fatalf("Token: %v", err)
	}

	stored, err := store.Load(cfg.ClientID)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if stored.AccessToken != "at-1" {
		t.Errorf("stored access token = %q, want at-1", stored.AccessToken)
	}
	if stored.RefreshToken != "rt-1" {
		t.Errorf("stored refresh token = %q, want the rotated rt-1", stored.RefreshToken)
	}
}

// A token that has not expired is used as it is — refreshing early spends a
// rotation for nothing.
func TestTokenSource_DoesNotRefreshALiveToken(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", t.TempDir())
	idp := newRotatingIDP(t, "rt-initial")
	cfg := config.Config{Issuer: idp.server.URL, ClientID: "icb-cli-archlinux"}
	store := &TokenStore{backend: newFakeKeyring()}
	if err := store.Save(cfg.ClientID, &oauth2.Token{
		AccessToken:  "at-live",
		RefreshToken: "rt-initial",
		TokenType:    "bearer",
		Expiry:       time.Now().Add(time.Hour),
	}); err != nil {
		t.Fatalf("seed the store: %v", err)
	}

	source, err := TokenSource(context.Background(), cfg, store)
	if err != nil {
		t.Fatalf("TokenSource: %v", err)
	}
	tok, err := source.Token()
	if err != nil {
		t.Fatalf("Token: %v", err)
	}
	if tok.AccessToken != "at-live" {
		t.Errorf("access token = %q, want the stored live one", tok.AccessToken)
	}
	if refreshes, _, _ := idp.counts(); refreshes != 0 {
		t.Errorf("refreshes = %d, want 0 for a live token", refreshes)
	}
}

// A grant Authelia has already revoked surfaces as an oauth2.RetrieveError, which
// is what the resource commands turn into the `icb auth login` hint.
func TestTokenSource_RevokedGrantSurfacesRetrieveError(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", t.TempDir())
	idp := newRotatingIDP(t, "rt-initial")
	cfg := config.Config{Issuer: idp.server.URL, ClientID: "icb-cli-archlinux"}
	store := &TokenStore{backend: newFakeKeyring()}
	seedExpiredToken(t, store, cfg.ClientID, "rt-stale")

	source, err := TokenSource(context.Background(), cfg, store)
	if err != nil {
		t.Fatalf("TokenSource: %v", err)
	}
	_, err = source.Token()
	if err == nil {
		t.Fatal("expected a refusal for a refresh token the provider does not hold")
	}
	var retrieveErr *oauth2.RetrieveError
	if !errors.As(err, &retrieveErr) {
		t.Fatalf("error was not an *oauth2.RetrieveError: %v", err)
	}
	if !strings.Contains(retrieveErr.Error(), "invalid_grant") {
		t.Errorf("error should carry invalid_grant, got: %v", retrieveErr)
	}
}
