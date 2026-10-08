package cli

import (
	"context"
	"errors"
	"fmt"
	"net/http"

	"github.com/datapointchris/goclilogin"
	"golang.org/x/oauth2"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/config"
)

// errNeedsLogin is returned by newAPIClient when there is no stored token. The
// resource commands print the login hint and exit 1; it is a normal state, not a
// crash, so it is kept distinct from a runtime error.
var errNeedsLogin = errors.New("not logged in")

// newAPIClient builds an authenticated API client. The oauth2 client injects
// (and refreshes) the bearer token on every request via goclilogin's token
// source, so resource commands never touch tokens directly.
func newAPIClient(ctx context.Context) (*api.Client, error) {
	cfg := config.Load()
	source, err := tokenSource(ctx, cfg)
	if errors.Is(err, errNeedsLogin) {
		return nil, err
	}
	if err != nil {
		return nil, fmt.Errorf("prepare API client: %w", err)
	}
	return api.New(cfg.APIBase, oauth2.NewClient(ctx, source)), nil
}

// tokenSource is the client-credentials grant when ICB_CLIENT_SECRET is set,
// and otherwise the token this machine logged in for.
func tokenSource(ctx context.Context, cfg config.Config) (oauth2.TokenSource, error) {
	if cfg.IsService() {
		return goclilogin.ClientCredentialsTokenSource(ctx, cfg.Service(), cfg.ClientSecret)
	}
	source, err := goclilogin.TokenSource(ctx, cfg.Login(), goclilogin.NewTokenStore(cfg.Login()))
	if errors.Is(err, goclilogin.ErrNotLoggedIn) {
		return nil, errNeedsLogin
	}
	return source, err
}

// handleAPIError maps an error from a resource command to a message and exit
// code: not-logged-in, a token endpoint that refused the refresh, and 401 all
// point at `icb auth login` (exit 1); everything else is a runtime error (exit 1
// via Execute). A service client is pointed at its id and secret instead,
// because no login exists for it. Returns the error to return from RunE.
func handleAPIError(err error) error {
	if errors.Is(err, errNeedsLogin) {
		return fmt.Errorf("not logged in — run `icb auth login`")
	}
	// A refusal at the token endpoint arrives as the transport error of the
	// request that triggered the refresh, so the URL and the raw OAuth error
	// description are what reach the terminal unless they are named here.
	if goclilogin.IsSessionRejected(err) {
		if cfg := config.Load(); cfg.IsService() {
			return fmt.Errorf("%s refused service client %s — check ICB_CLIENT_ID and ICB_CLIENT_SECRET", cfg.Issuer, cfg.ClientID)
		}
		return fmt.Errorf("session expired — run `icb auth login`")
	}
	var apiErr *api.APIError
	if errors.As(err, &apiErr) && apiErr.Unauthorized() {
		if cfg := config.Load(); cfg.IsService() {
			return fmt.Errorf("the API rejected the token issued to service client %s", cfg.ClientID)
		}
		return fmt.Errorf("session rejected by the API — run `icb auth login` to re-authenticate")
	}
	if errors.As(err, &apiErr) && apiErr.StatusCode == http.StatusConflict && apiErr.Message != "" {
		return refusal{apiErr}
	}
	return err
}

// refusal is a 409 the API explained. Its sentence is the whole error, printed
// without the "API request failed (409 Conflict):" prefix APIError adds.
type refusal struct{ *api.APIError }

func (r refusal) Error() string { return r.Message }

func (r refusal) Unwrap() error { return r.APIError }

// handleArgumentAPIError is handleAPIError for a resource whose arguments the
// API validates, so its 422 is a usage error.
//
// The API refuses an unknown vocabulary value with a 422 naming the values that
// would have worked. Left as a generic failure it exits 1, and a caller that
// retries on 1 and fixes its arguments on 2 retries a typo forever.
func handleArgumentAPIError(err error) error {
	var apiErr *api.APIError
	if errors.As(err, &apiErr) && apiErr.StatusCode == http.StatusUnprocessableEntity && apiErr.Message != "" {
		return usageError{errors.New(apiErr.Message)}
	}
	return handleAPIError(err)
}
