package config

// MIGRATION: this CLI was named icb. Everything here refuses a setting only a
// machine set up before the rename holds, and names what replaces it, because
// each one ignored would send a command somewhere it was not meant to go.

import (
	"errors"
	"fmt"
	"os"

	"github.com/datapointchris/goclikit"
	"github.com/datapointchris/goclilogin"
)

const formerProduct = "icb"

// formerClientSecretEnv selected the client-credentials grant. Ignored, a
// service would fall back to a person's login it cannot complete.
const formerClientSecretEnv = "ICB_CLIENT_SECRET"

// formerAPIBase pointed an earlier release at another API, dev among them.
// Ignored, a command meant for dev reaches the config file's API, which is
// production.
const formerAPIBase = "ICB_API_BASE"

func refuseFormerName() error {
	if os.Getenv(formerAPIBase) != "" {
		return goclikit.UsageError(fmt.Errorf("%s is set, and life does not read it: pass --api to point one command at another API, or unset it to use the config file's api", formerAPIBase))
	}
	if os.Getenv(formerClientSecretEnv) != "" {
		return goclikit.UsageError(fmt.Errorf("%s is set, and life reads %s: rename the variable", formerClientSecretEnv, ClientSecretEnv))
	}
	former := goclilogin.ConfigPath(formerProduct)
	if fileExists(former) && !fileExists(Path()) {
		return goclikit.UsageError(fmt.Errorf("%s holds icb's settings, and life reads %s: write its api, issuer and client_id there, where client_id is life-cli-<machine>", former, Path()))
	}
	return nil
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return !errors.Is(err, os.ErrNotExist)
}
