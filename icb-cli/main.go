package main

import (
	"os"

	"ichrisbirch/cli/internal/cli"
)

func main() {
	os.Exit(cli.Execute())
}
