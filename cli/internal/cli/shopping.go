package cli

import (
	"errors"
	"fmt"
	"io"
	"strings"
	"text/tabwriter"
	"time"
	"unicode/utf8"

	"github.com/spf13/cobra"

	"github.com/datapointchris/ichrisbirch/cli/internal/api"
	"github.com/datapointchris/ichrisbirch/cli/internal/prompt"
)

// shoppingPurchasesShown is the API's cap on a purchase-log read that sends no
// limit.
const shoppingPurchasesShown = 100

const unsortedLabel = "Unsorted"

func newShoppingCommand() *cobra.Command {
	cmd := asNamespace(&cobra.Command{
		Use:   "shopping",
		Short: "Your shopping list: items by section, checked off as you buy them",
		Long: "One list, split into sections such as stores or aisles. An item is a catalog\n" +
			"row that outlives the trip: checking it off records the purchase and takes it\n" +
			"off the list, and adding the same name later puts it back where it was.\n" +
			"\n" +
			"An item or a section is named by its name, in any case, or by its id.",
	})
	withNotFoundHints(cmd,
		"List what is on the list: icb shopping list",
		"List the whole catalog: icb shopping list --status all",
		"List every section: icb shopping sections list")
	cmd.AddCommand(
		newShoppingListCommand(),
		newShoppingAddCommand(),
		newShoppingCheckCommand(),
		newShoppingEditCommand(),
		newShoppingRemoveCommand(),
		newShoppingDeleteCommand(),
		newShoppingHistoryCommand(),
		newShoppingSectionsCommand(),
	)
	return cmd
}

func newShoppingListCommand() *cobra.Command {
	var (
		section string
		status  string
		asJSON  bool
		limit   int
	)
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List what is on the shopping list, by section",
		Long: "Items come back in list order: Unsorted first, then each section in the order\n" +
			"you arranged it. --status stocked lists the catalog items off the list, and\n" +
			"--status all lists both.",
		Example: "  icb shopping list\n" +
			"  icb shopping list --section costco\n" +
			"  icb shopping list --status all --json",
		Args: noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			if cmd.Flags().Changed("status") {
				canonical, err := prompt.OneOf(api.ShoppingItemStatuses)(status)
				if err != nil {
					return usageError{fmt.Errorf("--status: %w", err)}
				}
				status = canonical
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			filter := api.ShoppingItemFilter{Status: status, Section: section}
			items, err := client.ListShoppingItems(cmd.Context(), filter, limitFlag(cmd))
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), items)
			}
			if len(items) == 0 {
				_, _ = fmt.Fprintln(cmd.OutOrStdout(), emptyShoppingList(filter))
				return nil
			}
			printShoppingList(cmd.OutOrStdout(), items, status == "all")
			return nil
		},
	}
	cmd.Flags().StringVar(&section, "section", "", "Only this section, by name or id")
	cmd.Flags().StringVar(&status, "status", "", "needed (default), stocked, or all")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output items as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func emptyShoppingList(filter api.ShoppingItemFilter) string {
	what := "Nothing on the list"
	switch filter.Status {
	case "stocked":
		what = "Nothing in the catalog is off the list"
	case "all":
		what = "Nothing in the catalog"
	}
	if filter.Section != "" {
		return fmt.Sprintf("%s in %s.", what, filter.Section)
	}
	return what + "."
}

func newShoppingAddCommand() *cobra.Command {
	var (
		section string
		note    string
		asJSON  bool
	)
	cmd := &cobra.Command{
		Use:   "add [name...]",
		Short: "Put items on the shopping list",
		Long: "A name already in the catalog goes back on the list in the section and place\n" +
			"it held last time. A new name lands in Unsorted. --section puts every name\n" +
			"given at the end of that section instead, and --section \"\" puts them in\n" +
			"Unsorted.\n" +
			"\n" +
			"A --note on an item already on the list is added to the note it carries.\n" +
			"\n" +
			"Names are added in order, and the first that fails stops the rest. Run it\n" +
			"from a terminal with no names and it asks.",
		Example: "  icb shopping add eggs milk bananas\n" +
			"  icb shopping add \"wood glue\" --section hardware --note \"the yellow one\"\n" +
			"  icb shopping add",
		Args: cobra.ArbitraryArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			if len(args) == 0 && !interactive(cmd) {
				return usageError{fmt.Errorf("name an item, as in `icb shopping add eggs`, or run from a terminal to be asked")}
			}
			in := api.ShoppingItemAddInput{}
			var clear []string
			switch readFlagIntent(f, "section") {
			case flagClears:
				clear = append(clear, "section")
			case flagCarriesValues:
				in.Section = &section
			}
			if strings.TrimSpace(note) != "" {
				in.Note = &note
			}

			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			if len(args) == 0 {
				name, err := askShoppingItem(cmd, client, &in)
				if errors.Is(err, errAborted) {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "\nAborted.")
					return nil
				}
				if err != nil {
					return err
				}
				args = []string{name}
			}

			added := make([]api.ShoppingItem, 0, len(args))
			for _, name := range args {
				in.Name = name
				item, err := client.AddShoppingItem(cmd.Context(), in, clear)
				if err != nil {
					return handleArgumentAPIError(err)
				}
				added = append(added, item)
				if !asJSON {
					_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s → %s\n", item.Name, shoppingSectionLabel(item.SectionName))
				}
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), added)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&section, "section", "", "Section to put the items in, by name or id; \"\" is Unsorted")
	cmd.Flags().StringVar(&note, "note", "", "A note such as an amount, a brand, or a link")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the added items as JSON to stdout")
	return cmd
}

// askShoppingItem runs the guided add, asking only what no flag answered. The
// section choices are fetched, because sections are created and renamed freely.
func askShoppingItem(cmd *cobra.Command, client *api.Client, in *api.ShoppingItemAddInput) (string, error) {
	sections, err := client.ListShoppingSections(cmd.Context(), nil)
	if err != nil {
		return "", handleAPIError(err)
	}
	names := make([]string, 0, len(sections))
	for _, section := range sections {
		names = append(names, section.Name)
	}
	fields := []prompt.Field{{Key: "name", Label: "Item"}}
	if !cmd.Flags().Changed("section") && len(names) > 0 {
		fields = append(fields, prompt.Field{
			Key:      "section",
			Label:    "Section",
			Hint:     "Blank keeps a known item where it was, and puts a new one in Unsorted.",
			Choices:  names,
			Optional: true,
			Validate: prompt.OneOf(names),
		})
	}
	if !cmd.Flags().Changed("note") {
		fields = append(fields, prompt.Field{Key: "note", Label: "Note", Optional: true})
	}
	answers, err := runForm(cmd, prompt.Form{Intro: "Adding to the shopping list. Ctrl-C to abandon it.", Fields: fields})
	if err != nil {
		return "", err
	}
	if answers.Has("section") {
		in.Section = ptr(answers.Get("section"))
	}
	if answers.Has("note") {
		in.Note = ptr(answers.Get("note"))
	}
	return answers.Get("name"), nil
}

func newShoppingCheckCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:   "check <name>...",
		Short: "Check items off: record the purchase and take them off the list",
		Long: "Each name becomes a purchase in the log, which `icb shopping history` reads.\n" +
			"Names are checked in order, and the first that fails stops the rest.",
		Example: "  icb shopping check eggs milk",
		Args:    usageArgs(cobra.MinimumNArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			bought := make([]api.ShoppingPurchase, 0, len(args))
			for _, name := range args {
				purchase, err := client.CheckOffShoppingItem(cmd.Context(), name)
				if err != nil {
					return handleAPIError(err)
				}
				bought = append(bought, purchase)
				if !asJSON {
					_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Bought %s\n", purchase.ItemName)
				}
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), bought)
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the purchases as JSON to stdout")
	return cmd
}

func newShoppingEditCommand() *cobra.Command {
	var (
		name    string
		note    string
		section string
		asJSON  bool
	)
	cmd := &cobra.Command{
		Use:   "edit <name> [flags]",
		Short: "Rename an item, change its note, or move it to another section",
		Long: "Update only the fields whose flags you pass. --note \"\" removes the note, and\n" +
			"--section \"\" moves the item to Unsorted. A move puts it last in its new\n" +
			"section.",
		Example: "  icb shopping edit eggs --note \"2 dozen\"\n" +
			"  icb shopping edit \"wood glue\" --section hardware\n" +
			"  icb shopping edit tp --name \"toilet paper\"",
		Args: usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			in := api.ShoppingItemUpdateInput{}
			var clear []string
			switch readFlagIntent(f, "name") {
			case flagClears:
				return usageError{fmt.Errorf("--name cannot be empty — every item carries one")}
			case flagCarriesValues:
				in.Name = &name
			}
			if f.Changed("note") {
				in.Note = &note
			}
			switch readFlagIntent(f, "section") {
			case flagClears:
				clear = append(clear, "section")
			case flagCarriesValues:
				in.Section = &section
			}
			if in == (api.ShoppingItemUpdateInput{}) && len(clear) == 0 {
				return usageError{fmt.Errorf("nothing to change — pass at least one of --name/--note/--section")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.UpdateShoppingItem(cmd.Context(), args[0], in, clear)
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), item)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Updated %s → %s\n", item.Name, shoppingSectionLabel(item.SectionName))
			return nil
		},
	}
	cmd.Flags().StringVar(&name, "name", "", "New name")
	cmd.Flags().StringVar(&note, "note", "", "New note; \"\" removes it")
	cmd.Flags().StringVar(&section, "section", "", "Section to move the item to, by name or id; \"\" is Unsorted")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the updated item as JSON to stdout")
	return cmd
}

func newShoppingRemoveCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "remove <name>...",
		Short: "Take items off the list without buying them",
		Long: "The item stays in the catalog with its section and place, and no purchase is\n" +
			"recorded. Names are taken in order, and the first that fails stops the rest.",
		Example: "  icb shopping remove eggs",
		Args:    usageArgs(cobra.MinimumNArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			off := api.ShoppingItemUpdateInput{IsNeeded: ptr(false)}
			for _, name := range args {
				item, err := client.UpdateShoppingItem(cmd.Context(), name, off, nil)
				if err != nil {
					return handleAPIError(err)
				}
				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Took %s off the list\n", item.Name)
			}
			return nil
		},
	}
	return cmd
}

func newShoppingDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:   "delete <name>",
		Short: "Forget an item: remove it from the catalog",
		Long: "The item leaves the list and the catalog, so adding the name again starts it\n" +
			"in Unsorted. Its purchases stay in the log under the name they recorded.",
		Example: "  icb shopping delete \"hot plate for glue\" --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			item, err := client.GetShoppingItem(cmd.Context(), args[0])
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				question := fmt.Sprintf("Forget %s? Its %d purchases stay in the log.", item.Name, item.PurchaseCount)
				ok, err := confirm(cmd, question)
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteShoppingItem(cmd.Context(), item.ID); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Forgot %s\n", item.Name)
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func newShoppingHistoryCommand() *cobra.Command {
	var (
		start  string
		end    string
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:   "history",
		Short: "List what was bought, newest first",
		Long: "--start/--end bound the day of the purchase, inclusive on both ends, and\n" +
			"either works without the other. A day is read on this machine's calendar.",
		Example: "  icb shopping history\n" +
			"  icb shopping history --start 2026-10-01 --end 2026-10-31\n" +
			"  icb shopping history --limit 500 --json",
		Args: noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			for _, bound := range [][2]string{{"start", start}, {"end", end}} {
				if bound[1] == "" {
					continue
				}
				if err := validateDate(bound[1]); err != nil {
					return usageError{fmt.Errorf("--%s: %w", bound[0], err)}
				}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			purchases, err := client.ListShoppingPurchases(cmd.Context(),
				api.OnOrAfter(start), api.OnOrBefore(end), api.DayZone(LocalZoneName()), limitFlag(cmd))
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), purchases)
			}
			printShoppingHistory(cmd.OutOrStdout(), purchases)
			return nil
		},
	}
	cmd.Flags().StringVar(&start, "start", "", "Only purchases on or after this day (YYYY-MM-DD)")
	cmd.Flags().StringVar(&end, "end", "", "Only purchases on or before this day (YYYY-MM-DD)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output purchases as JSON to stdout")
	addServerCappedLimitFlag(cmd, &limit, shoppingPurchasesShown)
	return cmd
}

func newShoppingSectionsCommand() *cobra.Command {
	cmd := asNamespace(&cobra.Command{
		Use:   "sections",
		Short: "List, create, rename, reorder, and delete sections",
		Long: "A section is a part of the list such as a store or an aisle. Deleting one\n" +
			"moves its items to Unsorted.",
	})
	cmd.AddCommand(
		newShoppingSectionsListCommand(),
		newShoppingSectionsCreateCommand(),
		newShoppingSectionsRenameCommand(),
		newShoppingSectionsMoveCommand(),
		newShoppingSectionsDeleteCommand(),
	)
	return cmd
}

func newShoppingSectionsListCommand() *cobra.Command {
	var (
		asJSON bool
		limit  int
	)
	cmd := &cobra.Command{
		Use:     "list",
		Short:   "List sections in list order",
		Example: "  icb shopping sections list",
		Args:    noArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			sections, err := client.ListShoppingSections(cmd.Context(), limitFlag(cmd))
			if err != nil {
				return handleAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), sections)
			}
			if len(sections) == 0 {
				_, _ = fmt.Fprintln(cmd.OutOrStdout(), "No sections. Everything is in Unsorted.")
				return nil
			}
			for _, section := range sections {
				_, _ = fmt.Fprintln(cmd.OutOrStdout(), section.Name)
			}
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output sections as JSON to stdout")
	addLimitFlag(cmd, &limit)
	return cmd
}

func newShoppingSectionsCreateCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "create <name>",
		Short:   "Add a section at the end of the list",
		Example: "  icb shopping sections create Costco",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(args[0]) == "" {
				return usageError{fmt.Errorf("a section needs a name")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			section, err := client.CreateShoppingSection(cmd.Context(), args[0])
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), section)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Created section %s\n", section.Name)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the section as JSON to stdout")
	return cmd
}

func newShoppingSectionsRenameCommand() *cobra.Command {
	var asJSON bool
	cmd := &cobra.Command{
		Use:     "rename <section> <new-name>",
		Short:   "Rename a section",
		Example: "  icb shopping sections rename grocery \"Trader Joe's\"",
		Args:    usageArgs(cobra.ExactArgs(2)),
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(args[1]) == "" {
				return usageError{fmt.Errorf("a section needs a name")}
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			section, err := client.RenameShoppingSection(cmd.Context(), args[0], args[1])
			if err != nil {
				return handleArgumentAPIError(err)
			}
			if asJSON {
				return encodeJSON(cmd.OutOrStdout(), section)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Renamed %s to %s\n", args[0], section.Name)
			return nil
		},
	}
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output the section as JSON to stdout")
	return cmd
}

func newShoppingSectionsMoveCommand() *cobra.Command {
	var before, after string
	cmd := &cobra.Command{
		Use:     "move <section> (--before <section> | --after <section>)",
		Short:   "Move a section before or after another",
		Example: "  icb shopping sections move hardware --after costco",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			f := cmd.Flags()
			if f.Changed("before") == f.Changed("after") {
				return usageError{fmt.Errorf("pass exactly one of --before or --after")}
			}
			move := api.ShoppingSectionMove{}
			if f.Changed("before") {
				move.Before = &before
			} else {
				move.After = &after
			}
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			section, err := client.MoveShoppingSection(cmd.Context(), args[0], move)
			if err != nil {
				return handleArgumentAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Moved %s\n", section.Name)
			return nil
		},
	}
	cmd.Flags().StringVar(&before, "before", "", "Place it before this section")
	cmd.Flags().StringVar(&after, "after", "", "Place it after this section")
	return cmd
}

func newShoppingSectionsDeleteCommand() *cobra.Command {
	var yes bool
	cmd := &cobra.Command{
		Use:     "delete <section>",
		Short:   "Delete a section; its items move to Unsorted",
		Example: "  icb shopping sections delete hardware --yes",
		Args:    usageArgs(cobra.ExactArgs(1)),
		RunE: func(cmd *cobra.Command, args []string) error {
			client, err := newAPIClient(cmd.Context())
			if err != nil {
				return handleAPIError(err)
			}
			// The section's catalog rows are what the confirmation counts, and
			// reading them is also what refuses a section that does not exist.
			items, err := client.ListShoppingItems(cmd.Context(), api.ShoppingItemFilter{Status: "all", Section: args[0]}, nil)
			if err != nil {
				return handleAPIError(err)
			}
			if !yes {
				question := fmt.Sprintf("Delete section %s? Its %d items move to Unsorted.", args[0], len(items))
				ok, err := confirm(cmd, question)
				if err != nil {
					return err
				}
				if !ok {
					_, _ = fmt.Fprintln(cmd.ErrOrStderr(), "Aborted.")
					return nil
				}
			}
			if err := client.DeleteShoppingSection(cmd.Context(), args[0]); err != nil {
				return handleAPIError(err)
			}
			_, _ = fmt.Fprintf(cmd.OutOrStdout(), "Deleted section %s\n", args[0])
			return nil
		},
	}
	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip the confirmation prompt")
	return cmd
}

func shoppingSectionLabel(name *string) string {
	if name == nil {
		return unsortedLabel
	}
	return *name
}

// printShoppingList prints items under their section names. The API sends them
// grouped, so a new heading starts wherever the section changes. Notes line up
// in one column across the list, and a row without one carries no padding.
func printShoppingList(out io.Writer, items []api.ShoppingItem, markStocked bool) {
	names := make([]string, len(items))
	width := 0
	for i, item := range items {
		names[i] = item.Name
		if markStocked && !item.IsNeeded {
			names[i] += " (off the list)"
		}
		width = max(width, utf8.RuneCountInString(names[i]))
	}
	heading := ""
	for i, item := range items {
		if label := shoppingSectionLabel(item.SectionName); i == 0 || label != heading {
			heading = label
			_, _ = fmt.Fprintln(out, heading)
		}
		if note := strValue(item.Note); note != "" {
			_, _ = fmt.Fprintf(out, "  %-*s  %s\n", width, names[i], note)
		} else {
			_, _ = fmt.Fprintf(out, "  %s\n", names[i])
		}
	}
}

func printShoppingHistory(out io.Writer, purchases []api.ShoppingPurchase) {
	if len(purchases) == 0 {
		_, _ = fmt.Fprintln(out, "Nothing bought yet.")
		return
	}
	tw := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	_, _ = fmt.Fprintln(tw, "BOUGHT\tITEM\tSECTION\tNOTE")
	for _, p := range purchases {
		_, _ = fmt.Fprintf(tw, "%s\t%s\t%s\t%s\n",
			localMinute(p.PurchasedTS), p.ItemName, shoppingSectionLabel(p.SectionName), strValue(p.Note))
	}
	_ = tw.Flush()
}

// localMinute prints an instant to the minute on this machine's clock, or as
// it arrived when it does not parse.
func localMinute(instant string) string {
	t, err := time.Parse(time.RFC3339Nano, instant)
	if err != nil {
		return instant
	}
	return t.Local().Format("2006-01-02 15:04")
}
