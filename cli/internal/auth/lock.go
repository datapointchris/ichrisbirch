package auth

import (
	"os"
	"path/filepath"
	"time"

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

// lockWait bounds how long a process waits for the holder to finish. A refresh
// is one HTTP round trip, so a wait this long means the holder is wedged rather
// than busy.
const lockWait = 10 * time.Second

// lockPoll is how often a waiter retries. It is short enough that the common
// case — a holder that finishes in well under a second — is not padded by it.
const lockPoll = 20 * time.Millisecond

// lockRefresh takes an exclusive lock on path and returns the release. The lock
// lives on the open descriptor, so the kernel drops it when the process exits
// and a crash never leaves a lock file that blocks the next run.
//
// Every failure degrades to an unlocked refresh rather than to an unusable CLI:
// no home directory, an unwritable state directory, or a holder still wedged
// after lockWait. Unlocked is what the lock replaces, so falling back to it
// costs nothing that was not already being paid, whereas blocking forever on a
// wedged peer would be a worse failure than the race being prevented.
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
	if !acquire(file, lockWait) {
		_ = file.Close()
		return noop
	}
	return func() {
		_ = unix.Flock(int(file.Fd()), unix.LOCK_UN)
		_ = file.Close()
	}
}

// acquire polls for the exclusive lock until it is held or wait elapses. The
// non-blocking flag is what makes the deadline reachable — a plain LOCK_EX has
// no timeout and would park the process on a wedged holder indefinitely.
func acquire(file *os.File, wait time.Duration) bool {
	deadline := time.Now().Add(wait)
	for {
		if err := unix.Flock(int(file.Fd()), unix.LOCK_EX|unix.LOCK_NB); err == nil {
			return true
		}
		if time.Now().After(deadline) {
			return false
		}
		time.Sleep(lockPoll)
	}
}
