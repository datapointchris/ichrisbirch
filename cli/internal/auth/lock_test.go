package auth

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestLockRefresh_SerializesTwoHolders(t *testing.T) {
	path := filepath.Join(t.TempDir(), "icb-cli-test.refresh.lock")

	release := lockRefresh(path)
	defer release()

	// A second descriptor on the same file is what another process gets, and
	// flock is held per open file description rather than per process.
	second, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		t.Fatalf("open the lock a second time: %v", err)
	}
	defer func() { _ = second.Close() }()
	if acquire(second, 50*time.Millisecond) {
		t.Error("the second holder took a lock the first is holding")
	}
}

// Waiting forever on a wedged holder would be a worse failure than the race the
// lock prevents, so acquisition gives up and the caller refreshes unlocked.
func TestLockRefresh_GivesUpOnAWedgedHolder(t *testing.T) {
	path := filepath.Join(t.TempDir(), "icb-cli-test.refresh.lock")

	release := lockRefresh(path)
	defer release()

	done := make(chan struct{})
	go func() {
		defer close(done)
		lockRefreshBounded(path, 80*time.Millisecond)()
	}()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("a waiter blocked past its deadline")
	}
}

// lockRefreshBounded is lockRefresh with the wait injected, so the deadline test
// does not sit for the production lockWait.
func lockRefreshBounded(path string, wait time.Duration) func() {
	noop := func() {}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return noop
	}
	if !acquire(file, wait) {
		_ = file.Close()
		return noop
	}
	return func() { _ = file.Close() }
}

func TestLockRefresh_NoStateDirectoryStillRefreshes(t *testing.T) {
	// An empty path is what refreshLockPath returns when no home resolves. The
	// caller must still get a usable release rather than a nil dereference.
	release := lockRefresh("")
	if release == nil {
		t.Fatal("lockRefresh returned a nil release")
	}
	release()
}

func TestRefreshLockPath_IsPerClient(t *testing.T) {
	t.Setenv("XDG_STATE_HOME", "/tmp/xdgstate")
	got := refreshLockPath("icb-cli-archlinux")
	want := "/tmp/xdgstate/icb/icb-cli-archlinux.refresh.lock"
	if got != want {
		t.Errorf("refreshLockPath() = %q, want %q", got, want)
	}
	if refreshLockPath("icb-cli-mbp") == got {
		t.Error("two client ids resolved to the same lock file")
	}
}
