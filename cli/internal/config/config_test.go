package config

import (
	"testing"

	"github.com/datapointchris/goclilogin"
)

// Login is the seam between life's settings and goclilogin's, so what it carries
// across is worth pinning. The keyring service is a deployed identifier that
// several released versions already wrote under, and StateDir has to stay on
// life's own state directory rather than take goclilogin's default — two
// versions naming different lock files would not exclude each other during an
// upgrade.
func TestLoginCarriesTheDeployedIdentifiers(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")

	login := Login(goclilogin.Deployment{
		Issuer:   goclilogin.Setting{Value: "https://auth.example.com"},
		ClientID: goclilogin.Setting{Value: "life-cli-somehost"},
	})
	if login.Issuer != "https://auth.example.com" {
		t.Errorf("Issuer = %q", login.Issuer)
	}
	if login.ClientID != "life-cli-somehost" {
		t.Errorf("ClientID = %q", login.ClientID)
	}
	if login.KeyringService != "life-cli" {
		t.Errorf("KeyringService = %q, want life-cli", login.KeyringService)
	}
	if login.StateDir != "/tmp/xdgstate/life" {
		t.Errorf("StateDir = %q, want life's own state directory", login.StateDir)
	}
}

func TestStatePathIsTheToolsOwnStateDirectory(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")
	if got, want := StatePath(), "/tmp/xdgstate/life"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
	if got, want := StatePath("life-cli-archlinux.refresh.lock"), "/tmp/xdgstate/life/life-cli-archlinux.refresh.lock"; got != want {
		t.Errorf("StatePath(name) = %q, want %q", got, want)
	}
}

func TestStatePathFallsBackToLocalState(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "")
	t.Setenv("HOME", "/home/tester")
	if got, want := StatePath(), "/home/tester/.local/state/life"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
}
