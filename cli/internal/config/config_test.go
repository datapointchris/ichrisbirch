package config

import (
	"testing"

	"github.com/datapointchris/goclilogin"
)

// Login is the seam between icb's settings and goclilogin's, so what it carries
// across is worth pinning. The keyring service is a deployed identifier that
// several released versions already wrote under, and StateDir has to stay on
// icb's own state directory rather than take goclilogin's default — two
// versions naming different lock files would not exclude each other during an
// upgrade.
func TestLoginCarriesTheDeployedIdentifiers(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")

	login := Login(goclilogin.Deployment{
		Issuer:   goclilogin.Setting{Value: "https://auth.example.com"},
		ClientID: goclilogin.Setting{Value: "icb-cli-somehost"},
	})
	if login.Issuer != "https://auth.example.com" {
		t.Errorf("Issuer = %q", login.Issuer)
	}
	if login.ClientID != "icb-cli-somehost" {
		t.Errorf("ClientID = %q", login.ClientID)
	}
	if login.KeyringService != "icb-cli" {
		t.Errorf("KeyringService = %q, want icb-cli", login.KeyringService)
	}
	if login.StateDir != "/tmp/xdgstate/icb" {
		t.Errorf("StateDir = %q, want icb's own state directory", login.StateDir)
	}
}

func TestStatePathIsTheToolsOwnStateDirectory(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")
	if got, want := StatePath(), "/tmp/xdgstate/icb"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
	if got, want := StatePath("icb-cli-archlinux.refresh.lock"), "/tmp/xdgstate/icb/icb-cli-archlinux.refresh.lock"; got != want {
		t.Errorf("StatePath(name) = %q, want %q", got, want)
	}
}

func TestStatePathFallsBackToLocalState(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "")
	t.Setenv("HOME", "/home/tester")
	if got, want := StatePath(), "/home/tester/.local/state/icb"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
}
