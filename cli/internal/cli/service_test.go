package cli

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"regexp"
	"slices"
	"strings"
	"testing"

	"github.com/datapointchris/goclilogin"

	"github.com/datapointchris/ichrisbirch/cli/internal/config"
)

const (
	serviceClientID = "icb-svc-worker"
	serviceSecret   = "service-secret"
	serviceToken    = "service-access-token"
)

// serviceIDP grants a token only to serviceClientID presenting serviceSecret in
// a Basic header and naming exactly the scopes icb asks for. Anything else gets
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
		if r.FormValue("grant_type") != "client_credentials" || r.FormValue("scope") != "icb.project-items.read icb.issues.read icb.issues.close" {
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
	configure(t, api, idp, serviceClientID)
	t.Setenv(config.ClientSecretEnv, secret)
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
		Type     string `json:"type"`
		Session  string `json:"session"`
	}
	if err != nil || json.Unmarshal([]byte(out), &report) != nil || !report.LoggedIn || report.Type != "service_account" || report.Session != "live" {
		t.Errorf("status with a good secret: err %v, output %s, want logged in, service_account and live", err, out)
	}

	asService(t, idp.URL, "http://127.0.0.1:9", "wrong-secret")
	out, err = runService(t, "auth", "status")
	if exitCodeFor(err) != 1 || !strings.Contains(out, "ICB_CLIENT_SECRET") || strings.Contains(out, "auth login") {
		t.Errorf("status with a refused secret: exit %d, output %q, want 1 and the secret named", exitCodeFor(err), out)
	}
}

// A service stores no token, so with the provider down its next command fails
// too. A job gating on status has to see that.
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

func TestService_ARouteOutsideTheScopeReportsTheAPIsMessage(t *testing.T) {
	message := "Access denied: Route is outside this client's scopes; they reach only GET /api/v1/project-items"
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusForbidden)
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "Forbidden", "message": message})
	}))
	t.Cleanup(api.Close)
	asService(t, serviceIDP(t).URL, api.URL, serviceSecret)

	_, err := runService(t, "projects", "items", "search", "sync")
	if err == nil || !strings.Contains(err.Error(), serviceClientID) || !strings.Contains(err.Error(), message) || strings.Contains(err.Error(), "auth login") {
		t.Errorf("got %v, want the client and the API's message whole, and no login suggested", err)
	}
}

// serviceIDP grants the scopes this file spells, which is the CLI's own copy.
// So a scope the API renamed, or a route one of these calls sends that the API
// stopped listing, passes every other test here and answers 403 to every
// scheduled run.
func TestService_EachScheduledCallSendsARouteTheRequestedScopesReach(t *testing.T) {
	raw, err := os.ReadFile("../../../tests/ichrisbirch/api/testdata/client-scopes.json")
	if err != nil {
		t.Fatalf("read the API's scope table — run tests/ichrisbirch/api/test_client_scopes.py to write it: %v", err)
	}
	var reaches map[string][]string
	if err := json.Unmarshal(raw, &reaches); err != nil {
		t.Fatalf("decode the API's scope table: %v", err)
	}

	// A {name} in these templates is a UUID, or for an issue its number. Matched
	// as any segment, /project-items/{id} would also take /project-items/search
	// and /issues/{id} would take /issues/vocabulary, both of which FastAPI
	// routes to another handler. A {name:path} is FastAPI's path converter, which
	// takes any segments, and an initiative is named by its name.
	reference := `(?:[0-9]+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`
	wildcard := regexp.MustCompile(`\{[^}]*\}`)
	scopes := config.Service(goclilogin.Deployment{}).Scopes
	var listed []*regexp.Regexp
	for _, scope := range scopes {
		for _, template := range reaches[scope] {
			var pattern strings.Builder
			last := 0
			for _, at := range wildcard.FindAllStringIndex(template, -1) {
				pattern.WriteString(regexp.QuoteMeta(template[last:at[0]]))
				if strings.HasSuffix(template[at[0]:at[1]], ":path}") {
					pattern.WriteString(".+")
				} else {
					pattern.WriteString(reference)
				}
				last = at[1]
			}
			pattern.WriteString(regexp.QuoteMeta(template[last:]))
			listed = append(listed, regexp.MustCompile("^"+pattern.String()+"$"))
		}
	}

	idp := serviceIDP(t)
	openIssue := `{"id":"019a2b3c-4d5e-7f60-8a9b-0c1d2e3f4a5b","number":412,"title":"t","status":"open"}`
	for _, call := range []struct {
		args []string
		body string
		// byPath answers a call that makes a second request of another shape.
		byPath map[string]string
	}{
		{[]string{"projects", "items", "search", "sync"}, `[]`, nil},
		{[]string{"issues", "search", "sync", "--json"}, `[]`, nil},
		{[]string{"issues", "list", "--json"}, `[]`, nil},
		{[]string{"issues", "list", "--blocked", "--json"}, `[]`, nil},
		{[]string{"issues", "next", "--json"}, `[]`, nil},
		{[]string{"issues", "show", "412", "--json"}, `{}`, nil},
		{[]string{"issues", "show", "019a2b3c-4d5e-7f60-8a9b-0c1d2e3f4a5b", "--json"}, `{}`, nil},
		{[]string{"issues", "initiatives", "list", "--json"}, `[]`, nil},
		{
			[]string{"issues", "initiatives", "show", "Practical help guides", "--json"},
			`[]`,
			map[string]string{"/api/v1/issues/initiatives/Practical help guides": `{}`},
		},
		{[]string{"issues", "add-comment", "412", "--body", "Landed: a merged fix"}, `{}`, nil},
		{[]string{"issues", "complete", "412"}, openIssue, nil},
	} {
		t.Run(strings.Join(call.args, " "), func(t *testing.T) {
			var sent []string
			api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				sent = append(sent, r.Method+" "+r.URL.Path)
				w.Header().Set("Content-Type", "application/json")
				body, ok := call.byPath[r.URL.Path]
				if !ok {
					body = call.body
				}
				_, _ = w.Write([]byte(body))
			}))
			t.Cleanup(api.Close)
			asService(t, idp.URL, api.URL, serviceSecret)
			if _, err := runService(t, call.args...); err != nil {
				t.Fatalf("run as a service: %v", err)
			}
			if len(sent) == 0 {
				t.Fatal("sent nothing to hold against the scopes")
			}
			for _, request := range sent {
				if !slices.ContainsFunc(listed, func(re *regexp.Regexp) bool { return re.MatchString(request) }) {
					t.Errorf("sent %s, which the API lists for none of %v", request, scopes)
				}
			}
		})
	}
}
