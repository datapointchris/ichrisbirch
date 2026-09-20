package cli

import (
	"os"
	"path/filepath"
	"strings"
)

// zoneinfoDirs are the paths a tzdata file lives under. The IANA name is
// whatever follows one of them, so "/usr/share/zoneinfo/US/Eastern" is
// "US/Eastern". macOS ships the same tree under /var/db/timezone.
var zoneinfoDirs = []string{
	"/usr/share/zoneinfo/",
	"/usr/lib/zoneinfo/",
	"/usr/share/lib/zoneinfo/",
	"/var/db/timezone/zoneinfo/",
}

// LocalZoneName is the IANA name of this machine's timezone, or "" when it
// cannot be read.
//
// time.Local carries the right offset rules but not the name: Go reports
// "Local" for a zone loaded from /etc/localtime, and the server needs a name it
// can look up. So this reads the two places the name is actually written — $TZ,
// then the symlink target of /etc/localtime.
//
// An empty return is not a failure to report. The caller leaves the parameter
// off, the server reads the day in UTC, and the response says so — a visibly
// wrong zone beats a silently wrong day.
func LocalZoneName() string {
	if name := zoneFromEnv(os.Getenv("TZ")); name != "" {
		return name
	}
	return zoneFromLocaltimeLink("/etc/localtime")
}

// zoneFromEnv reads $TZ. A leading colon is allowed by POSIX and is part of the
// spelling rather than the name. A value that is an absolute path is a tzdata
// file, so it goes through the same trimming as the symlink.
func zoneFromEnv(tz string) string {
	tz = strings.TrimPrefix(tz, ":")
	if tz == "" || tz == "Local" {
		return ""
	}
	if strings.HasPrefix(tz, "/") {
		return trimZoneinfoDir(tz)
	}
	return tz
}

// zoneFromLocaltimeLink resolves /etc/localtime to the tzdata file it names.
// A copy rather than a symlink — which is what a container image usually ships
// — carries no name, so this returns "".
func zoneFromLocaltimeLink(path string) string {
	target, err := filepath.EvalSymlinks(path)
	if err != nil {
		return ""
	}
	return trimZoneinfoDir(target)
}

// trimZoneinfoDir turns a tzdata path into the IANA name under it, or "" when
// the path sits outside every known zoneinfo tree.
func trimZoneinfoDir(path string) string {
	for _, dir := range zoneinfoDirs {
		if name, found := strings.CutPrefix(path, dir); found && name != "" {
			return name
		}
	}
	return ""
}
