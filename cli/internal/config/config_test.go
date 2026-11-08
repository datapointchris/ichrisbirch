package config

import (
	"testing"

	"github.com/datapointchris/goclilogin"
)

// The refresh lock lives in life's own state directory, and Login hands that
// directory to goclilogin rather than letting it default to one named for the
// keyring service.
func TestStatePathIsTheToolsOwnStateDirectory(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")
	if got, want := StatePath(), "/tmp/xdgstate/life"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
	if got, want := StatePath("life-cli-archlinux.refresh.lock"), "/tmp/xdgstate/life/life-cli-archlinux.refresh.lock"; got != want {
		t.Errorf("StatePath(name) = %q, want %q", got, want)
	}
	if got := Login(goclilogin.Deployment{}).StateDir; got != StatePath() {
		t.Errorf("Login().StateDir = %q, want %q", got, StatePath())
	}
}

func TestStatePathFallsBackToLocalState(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "")
	t.Setenv("HOME", "/home/tester")
	if got, want := StatePath(), "/home/tester/.local/state/life"; got != want {
		t.Errorf("StatePath() = %q, want %q", got, want)
	}
}
