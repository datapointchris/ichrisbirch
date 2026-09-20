package cli

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// time.Local carries the right offset rules but reports "Local" as its name on
// every machine that loads a zone from /etc/localtime. That is the whole reason
// this file exists, so it is worth pinning: if Go ever starts reporting the IANA
// name, LocalZoneName can be deleted.
func TestTimeLocalDoesNotCarryTheIANAName(t *testing.T) {
	if name := time.Local.String(); name != "Local" && os.Getenv("TZ") == "" {
		t.Logf("time.Local.String() = %q — Go now names the zone, so LocalZoneName may be redundant", name)
	}
}

func TestZoneFromEnv(t *testing.T) {
	cases := []struct {
		name string
		tz   string
		want string
	}{
		{"a plain name", "America/New_York", "America/New_York"},
		{"a leading colon is POSIX spelling, not part of the name", ":America/New_York", "America/New_York"},
		{"an absolute path is a tzdata file", "/usr/share/zoneinfo/US/Eastern", "US/Eastern"},
		{"unset", "", ""},
		{"Go's own placeholder is not a zone name", "Local", ""},
		{"a path outside every zoneinfo tree names nothing", "/opt/custom/EST5EDT", ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := zoneFromEnv(tc.tz); got != tc.want {
				t.Errorf("zoneFromEnv(%q) = %q, want %q", tc.tz, got, tc.want)
			}
		})
	}
}

func TestTrimZoneinfoDir_ReadsEveryKnownTree(t *testing.T) {
	cases := map[string]string{
		"/usr/share/zoneinfo/US/Eastern":              "US/Eastern",
		"/var/db/timezone/zoneinfo/America/New_York":  "America/New_York",
		"/usr/lib/zoneinfo/Europe/Berlin":             "Europe/Berlin",
		"/usr/share/lib/zoneinfo/Australia/Melbourne": "Australia/Melbourne",
		"/etc/localtime":                              "",
		"/usr/share/zoneinfo/":                        "",
	}
	for path, want := range cases {
		if got := trimZoneinfoDir(path); got != want {
			t.Errorf("trimZoneinfoDir(%q) = %q, want %q", path, got, want)
		}
	}
}

func TestZoneFromLocaltimeLink_ReadsTheSymlinkTarget(t *testing.T) {
	dir := t.TempDir()
	tzfile := filepath.Join(dir, "usr", "share", "zoneinfo", "US", "Eastern")
	if err := os.MkdirAll(filepath.Dir(tzfile), 0o755); err != nil {
		t.Fatalf("building the fake tree: %v", err)
	}
	if err := os.WriteFile(tzfile, []byte("TZif"), 0o644); err != nil {
		t.Fatalf("writing the fake tzdata file: %v", err)
	}
	link := filepath.Join(dir, "localtime")
	if err := os.Symlink(tzfile, link); err != nil {
		t.Fatalf("linking: %v", err)
	}

	// The temp dir is not under a real zoneinfo tree, so the name is not found —
	// which is the point of the assertion below, not a flaw in the fixture.
	if got := zoneFromLocaltimeLink(link); got != "" {
		t.Errorf("zoneFromLocaltimeLink = %q, want \"\" for a tree outside the known paths", got)
	}
}

// A copy rather than a symlink carries no name, which is what a container image
// usually ships. The caller leaves the parameter off and the server reads the day
// in UTC, which the response then says.
func TestZoneFromLocaltimeLink_ACopyNamesNothing(t *testing.T) {
	dir := t.TempDir()
	copied := filepath.Join(dir, "localtime")
	if err := os.WriteFile(copied, []byte("TZif"), 0o644); err != nil {
		t.Fatalf("writing: %v", err)
	}

	if got := zoneFromLocaltimeLink(copied); got != "" {
		t.Errorf("zoneFromLocaltimeLink = %q, want \"\"", got)
	}
}

func TestZoneFromLocaltimeLink_AMissingFileNamesNothing(t *testing.T) {
	if got := zoneFromLocaltimeLink(filepath.Join(t.TempDir(), "absent")); got != "" {
		t.Errorf("zoneFromLocaltimeLink = %q, want \"\"", got)
	}
}

// $TZ outranks the symlink, because a process that sets it means it.
func TestLocalZoneName_PrefersTZ(t *testing.T) {
	t.Setenv("TZ", "Asia/Tokyo")

	if got := LocalZoneName(); got != "Asia/Tokyo" {
		t.Errorf("LocalZoneName = %q, want Asia/Tokyo", got)
	}
}
