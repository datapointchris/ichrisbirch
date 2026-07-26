package main

import (
	"os"

	"github.com/datapointchris/ichrisbirch/cli/internal/cli"
)

func main() {
	os.Exit(cli.Execute())
}
