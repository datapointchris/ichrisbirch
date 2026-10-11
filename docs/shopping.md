# Shopping List

The shopping list is one list split into sections, such as a store or an aisle.
It lives in its own Postgres schema, `shopping`, with three tables: `sections`,
`items` and `purchases`.

## An item is a catalog row that outlives the trip

`shopping.items` holds everything ever put on the list, not only what is on it
now. `is_needed` says whether an item is on the list. Checking an item off sets
`is_needed` false and writes a row to `shopping.purchases`. The item row stays.

Adding a name already in the catalog lists that row again rather than creating
one. It returns in the section and the place it held, because both stayed on the
row while it was off the list. So "eggs" comes back beside "milk" in Costco
without being placed there again. A new name lands in Unsorted, which is a null
`section_id`.

`POST /shopping/items` answers 201 for a new name and 200 for a known one.
Sending a different `section` moves the item to the end of that section, and a
null `section` moves it to Unsorted. Omitting `section`, or sending the one it
is in, keeps it where it was.

Names are unique ignoring case, through a unique index on `lower(name)`. So an
item or a section is addressed by its name as well as its UUID, in the path and
in the CLI. A name that matches nothing answers 404 with the nearest names.
The reference is declared as a path rather than one segment. A client escapes
the slash in a name such as "Fruit/Veg", and the server decodes it before
routing, so a one-segment reference would never match that name.

## Order is a float rank, so a hidden row keeps its place

An item's position is a `rank` float, and so is a section's. Moving a row writes
one value, the midpoint of its new neighbors' ranks. When the gap between two
neighbors falls under `MIN_GAP`, the table is renumbered to whole numbers and
the move is retried. `services/fractional_rank.py` holds this, and issues use
the same service.

An integer position would not work here. The ordered set includes the items off
the list, which no client sees. A client dropping "eggs" between two visible
rows cannot know which hidden rows sit between them, so it cannot name an
integer position that keeps them in order. A float rank needs only the
neighbors the client saw.

Each table has one rank space, shared by every section. The list order is
section rank, then item rank:

```sql
ORDER BY sections.rank NULLS FIRST, items.rank
```

Placing an item after a visible neighbor A takes the midpoint of A's rank and
the next rank anywhere in the table. Rows of other sections can sit in that
gap, but nothing of A's section can, because the next rank in the table is at
least as close as the next rank in A's section. So one rank space keeps every
section's order, and a cross-section drag is one request:
`POST /shopping/items/{ref}/rank` with the section and one neighbor.

## A purchase copies what it needs to read the same later

A purchase stores `item_name`, `note` and `section_name` as they were at the
check-off. Its `item_id` is set null when the item is deleted. So the log reads
the same after an item is renamed, moved or forgotten.

Checking off consumes the item's note, because "2 dozen" described that trip.
Deleting the purchase is the undo. It lists the item again and restores the note
the purchase copied, unless the item went back on the list in the meantime.

A note added to an item already on the list is appended to its note once,
joined by `; `. Two recipes asking for onions then both stay readable.

The page's "Recently bought" footer is a purchases read bounded to the last
`RECENT_PURCHASE_DAYS` days in the user's zone, grouped under the day each was
made, so it survives the app being closed. Tapping a row there is the undo. The
window runs past today because a mistaken check-off is often noticed only on
the next trip, and the page is where it gets noticed. A purchases read sent
without a limit returns the newest `PURCHASES_SHOWN` rows, because the log only
grows.

## The page is built for a phone

`/shopping` is meant to be used from a phone's home screen. Every control is at
least 44px tall, rows are dragged by a grip with `touch-action: none` so the page
still scrolls, and a quick add keeps the keyboard up. The app shell supplies the
rest: a web manifest and icons, and a sidebar that goes off-canvas under the
`--phone-max-width` breakpoint. There is no service worker, so the page needs
the network.

`RecipeDetailView` adds a recipe's ingredients to the list at its current
servings. Each item is noted with its amount and the recipe's name.
