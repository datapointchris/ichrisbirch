package main

import (
	"os"

	"github.com/datapointchris/life/cli/internal/cli"
)

func main() {
	os.Exit(cli.Execute())
}
