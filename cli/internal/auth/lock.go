package auth

import (
	"os"
	"path/filepath"

	"golang.org/x/sys/unix"

	"github.com/datapointchris/ichrisbirch/cli/internal/config"
)

// refreshLockPath is the machine-wide lock every icb process contends for before
// it refreshes. It is keyed by client_id so two deployments configured on one
// machine hold separate locks.
func refreshLockPath(clientID string) string {
	dir := config.StatePath()
	if dir == "" {
		return ""
	}
	return filepath.Join(dir, clientID+".refresh.lock")
}

// lockRefresh takes an exclusive lock on path and returns the release. The lock
// lives on the open descriptor, so the kernel drops it when the process exits
// and a crash never leaves a lock file that blocks the next run.
//
// A machine that cannot host the lock at all — no home directory, an unwritable
// state directory — gets an unlocked refresh rather than an unusable CLI. That
// is the behavior the lock replaces, so degrading to it costs nothing that was
// not already being paid.
func lockRefresh(path string) func() {
	noop := func() {}
	if path == "" {
		return noop
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return noop
	}
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return noop
	}
	if err := unix.Flock(int(file.Fd()), unix.LOCK_EX); err != nil {
		_ = file.Close()
		return noop
	}
	return func() {
		_ = unix.Flock(int(file.Fd()), unix.LOCK_UN)
		_ = file.Close()
	}
}
