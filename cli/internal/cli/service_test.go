package cli

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

const (
	serviceClientID = "icb-svc-worker"
	serviceSecret   = "service-secret"
	serviceToken    = "service-access-token"
)

// serviceIDP grants a token only to serviceClientID presenting serviceSecret in
// a Basic header and naming exactly the scope icb asks for. Anything else gets
// the refusal Authelia sends.
func serviceIDP(t *testing.T) *httptest.Server {
	t.Helper()
	var srv *httptest.Server
	mux := http.NewServeMux()
	mux.HandleFunc("/.well-known/openid-configuration", func(w http.ResponseWriter, _ *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]string{"issuer": srv.URL, "token_endpoint": srv.URL + "/token"})
	})
	mux.HandleFunc("/token", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		id, secret, ok := r.BasicAuth()
		if !ok || id != serviceClientID || secret != serviceSecret {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":"invalid_client"}`))
			return
		}
		if r.FormValue("grant_type") != "client_credentials" || r.FormValue("scope") != "icb.project-items.read" {
			w.WriteHeader(http.StatusBadRequest)
			_, _ = w.Write([]byte(`{"error":"invalid_scope"}`))
			return
		}
		_, _ = w.Write([]byte(`{"access_token":"` + serviceToken + `","token_type":"bearer","expires_in":300}`))
	})
	srv = httptest.NewServer(mux)
	t.Cleanup(srv.Close)
	return srv
}

// asService points icb at idp and api as serviceClientID holding secret, with a
// state directory the test can inspect afterwards.
func asService(t *testing.T, idp, api, secret string) string {
	t.Helper()
	state := t.TempDir()
	t.Setenv("XDG_STATE_HOME", state)
	t.Setenv("ICB_OIDC_ISSUER", idp)
	t.Setenv("ICB_API_BASE", api)
	t.Setenv("ICB_CLIENT_ID", serviceClientID)
	t.Setenv("ICB_CLIENT_SECRET", secret)
	return state
}

func runService(t *testing.T, args ...string) (string, error) {
	t.Helper()
	root := NewRootCommand()
	var out bytes.Buffer
	root.SetOut(&out)
	root.SetErr(&bytes.Buffer{})
	root.SetArgs(args)
	err := root.Execute()
	return out.String(), err
}

func TestService_SearchCarriesTheClientCredentialsToken(t *testing.T) {
	var authorization string
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authorization = r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`[]`))
	}))
	t.Cleanup(api.Close)
	state := asService(t, serviceIDP(t).URL, api.URL, serviceSecret)

	if _, err := runService(t, "projects", "items", "search", "sync"); err != nil {
		t.Fatalf("search as a service: %v", err)
	}
	if authorization != "Bearer "+serviceToken {
		t.Errorf("the API saw Authorization %q, want the service token", authorization)
	}
	entries, _ := os.ReadDir(state)
	if len(entries) != 0 {
		t.Errorf("a service run wrote %v under its state directory, want nothing stored", entries)
	}
}

func TestService_ARefusedSecretNamesTheSecretRatherThanALogin(t *testing.T) {
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		t.Error("the API was called without a token")
	}))
	t.Cleanup(api.Close)
	asService(t, serviceIDP(t).URL, api.URL, "wrong-secret")

	_, err := runService(t, "projects", "items", "search", "sync")
	if err == nil || !strings.Contains(err.Error(), "ICB_CLIENT_SECRET") || strings.Contains(err.Error(), "auth login") {
		t.Errorf("got %v, want the secret named and no login suggested", err)
	}
}

func TestService_StatusAsksTheProvider(t *testing.T) {
	idp := serviceIDP(t)

	asService(t, idp.URL, "http://127.0.0.1:9", serviceSecret)
	out, err := runService(t, "auth", "status", "--json")
	var report struct {
		LoggedIn bool   `json:"logged_in"`
		Mode     string `json:"mode"`
		Session  string `json:"session"`
	}
	if err != nil || json.Unmarshal([]byte(out), &report) != nil || !report.LoggedIn || report.Mode != "service" || report.Session != "live" {
		t.Errorf("status with a good secret: err %v, output %s, want logged in, service and live", err, out)
	}

	asService(t, idp.URL, "http://127.0.0.1:9", "wrong-secret")
	out, err = runService(t, "auth", "status")
	if exitCodeFor(err) != 1 || !strings.Contains(out, "ICB_CLIENT_SECRET") || strings.Contains(out, "auth login") {
		t.Errorf("status with a refused secret: exit %d, output %q, want 1 and the secret named", exitCodeFor(err), out)
	}
}

// A service stores no token, so a provider it cannot reach means the next
// command fails, and a job gating on status has to see that.
func TestService_StatusWithTheProviderDownExitsOne(t *testing.T) {
	asService(t, "http://127.0.0.1:9", "http://127.0.0.1:9", serviceSecret)
	out, err := runService(t, "auth", "status", "--json")
	var report struct {
		LoggedIn bool   `json:"logged_in"`
		Session  string `json:"session"`
	}
	if exitCodeFor(err) != 1 || json.Unmarshal([]byte(out), &report) != nil || report.LoggedIn || report.Session != "unverified" {
		t.Errorf("status with the provider down: exit %d, output %s, want 1, not logged in, unverified", exitCodeFor(err), out)
	}
}

func TestService_LoginAndLogoutAreRefused(t *testing.T) {
	asService(t, serviceIDP(t).URL, "http://127.0.0.1:9", serviceSecret)
	for _, verb := range []string{"login", "logout"} {
		_, err := runService(t, "auth", verb)
		if err == nil || !strings.Contains(err.Error(), "ICB_CLIENT_SECRET") {
			t.Errorf("auth %s: got %v, want it refused with the secret named", verb, err)
		}
	}
}

// Without ICB_CLIENT_ID the client would be the person's icb-cli-<host>.
func TestService_ASecretWithoutItsClientIsRefused(t *testing.T) {
	asService(t, serviceIDP(t).URL, "http://127.0.0.1:9", serviceSecret)
	t.Setenv("ICB_CLIENT_ID", "")
	for _, args := range [][]string{{"projects", "items", "search", "sync"}, {"auth", "status"}, {"auth", "token"}} {
		_, err := runService(t, args...)
		if err == nil || !strings.Contains(err.Error(), "ICB_CLIENT_ID") {
			t.Errorf("%v: got %v, want it refused naming ICB_CLIENT_ID", args, err)
		}
	}
}

func TestService_ARouteOutsideTheScopeNamesTheScope(t *testing.T) {
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusForbidden)
		_, _ = w.Write([]byte(`{"detail":"Route is outside this client's scopes"}`))
	}))
	t.Cleanup(api.Close)
	asService(t, serviceIDP(t).URL, api.URL, serviceSecret)

	_, err := runService(t, "projects", "items", "search", "sync")
	if err == nil || !strings.Contains(err.Error(), serviceClientID) || !strings.Contains(err.Error(), "icb projects items") {
		t.Errorf("got %v, want the client and what its scope covers named", err)
	}
}
