"""Seed cooking techniques — reusable cooking patterns referenced by recipes."""

from __future__ import annotations

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.recipe import COOKING_TECHNIQUE_CATEGORIES
from ichrisbirch.models.recipe import CookingTechnique
from ichrisbirch.models.recipe import CookingTechniqueCategory
from ichrisbirch.util import slugify
from scripts.seed.base import SeedResult

COOKING_TECHNIQUE_BLUEPRINTS: list[dict] = [
    {
        'name': '3:1 Vinaigrette Ratio',
        'category': 'composition_and_ratio',
        'summary': (
            'The canonical vinaigrette is 3 parts fat to 1 part acid, emulsified with something to hold it together '
            '(mustard, egg yolk, puréed aromatics). Scale the ratio, swap the fat or acid, and you have a template that '
            'covers chimichurri, Caesar dressing, aioli, and a dozen other sauces.'
        ),
        'body': (
            '## The Ratio\n\n'
            '- **3 parts fat**: olive oil, neutral oil, nut oils, melted butter for warm dressings.\n'
            '- **1 part acid**: vinegar (red wine, sherry, rice, apple cider) or citrus juice.\n'
            '- **Emulsifier** (optional but makes it stable): Dijon mustard, egg yolk, minced shallot, mortar-pounded garlic paste.\n'
            '- **Salt, pepper, aromatics** to taste.\n\n'
            '## Why This Ratio\n\n'
            'More acid makes your mouth pucker; less makes the dressing taste flat and greasy. 3:1 is where the tongue '
            'reads "bright but balanced." Restaurants that make their own dressings hit this ratio almost every time.\n\n'
            '## Building a Chimichurri From This\n\n'
            '3 parts olive oil : 1 part red wine vinegar + lemon juice, with packed fresh parsley, oregano, garlic, '
            'shallot, and red pepper flakes pounded into a paste first.'
        ),
        'why_it_works': (
            'Oil coats the tongue and carries fat-soluble flavor compounds. Acid provides volatility and brightness. '
            'Too much acid overwhelms; too little and the oil tastes heavy. The 3:1 balance matches how human taste '
            'receptors weigh the two.'
        ),
        'common_pitfalls': (
            'Adding acid and oil at the same time without an emulsifier — the dressing separates in 30 seconds. '
            'Whisk acid + mustard + salt first, THEN drizzle oil slowly while whisking to build the emulsion.'
        ),
        'tags': ['sauce', 'emulsion', 'framework', 'ratio'],
        'rating': 5,
    },
    {
        'name': 'Caramelize Tomato Paste Before Adding Liquids',
        'category': 'flavor_development',
        'summary': (
            'Before you pour stock or water into a stew, fry the tomato paste in the fat with your aromatics until it '
            'darkens to a brick-red color. This Maillard-like browning takes 2-3 minutes and adds a depth of flavor '
            'that no amount of simmering can replicate.'
        ),
        'body': (
            '## The Technique\n\n'
            '1. After sweating onions/garlic, push them to the side of the pan.\n'
            '2. Add 1-2 tbsp tomato paste directly onto the hot surface of the pan.\n'
            '3. Stir and smear it around for 2-3 minutes until it visibly darkens from bright red to brick or rust red.\n'
            '4. You may see it stick slightly — that fond is good, it deglazes into the stew.\n'
            '5. NOW add your liquid. The paste should dissolve into the broth and disappear, its flavor spread throughout.\n\n'
            '## When to Use\n\n'
            'Any time a recipe calls for tomato paste in a long-cooked dish: stews, braises, bolognese, chili, '
            'shakshuka, beans, lentil soups.'
        ),
        'why_it_works': (
            'Tomato paste contains sugars and amino acids. Heating it drives off water and allows Maillard reactions '
            'and caramelization to occur, producing nutty, complex flavor compounds that simply dumping the paste into '
            'liquid cannot generate.'
        ),
        'common_pitfalls': (
            'Going too long and burning it — past rust-red into black is acrid and bitter. If you smell it sharpen, add liquid immediately.'
        ),
        'tags': ['stew', 'braise', 'maillard', 'aromatic-base'],
        'rating': 5,
    },
    {
        'name': '24-Hour Bean Soak',
        'category': 'preservation_and_pre_treatment',
        'summary': (
            'Dried beans soaked in salted water for 24 hours (changing the water once) cook faster, digest easier, and '
            'have their antinutrients (phytic acid, lectins, oligosaccharides) significantly reduced. The texture is '
            'also dramatically better — creamier interior, intact skins.'
        ),
        'body': (
            '## The Technique\n\n'
            '1. Rinse dried beans and cover with cold water by 3 inches.\n'
            '2. Add 1 tbsp salt per pound of beans (salt does NOT make skins tough — that myth is debunked).\n'
            '3. Soak at room temp 12-24 hours. Swap the water once at the halfway point if possible.\n'
            '4. Drain, rinse, cook in fresh water or broth.\n\n'
            '## Quick Soak Alternative\n\n'
            'Boil for 2 min, remove from heat, soak 1 hour. Works but the 24-hour method yields better texture.'
        ),
        'why_it_works': (
            'Phytic acid (which binds minerals and blocks absorption) is partially broken down during long soaks. '
            "Oligosaccharides (the cause of digestive discomfort) leach into the soaking water — that's why you dump "
            'it. Lectins degrade with soak + cook. Salt helps skin permeability so beans hydrate evenly.'
        ),
        'common_pitfalls': (
            "Cooking the beans in the soaking water — defeats the point; dump it. Also, old beans (2+ years) won't "
            'soften no matter how long you soak them.'
        ),
        'tags': ['beans', 'legumes', 'soak', 'digestion'],
        'rating': 5,
    },
    {
        'name': 'Mortar-and-Pestle Aromatic Paste',
        'category': 'flavor_development',
        'summary': (
            'Pounding garlic, salt, herbs, and spices into a paste with a mortar and pestle releases essential oils '
            'that simply mincing cannot. The resulting paste integrates into dressings, marinades, and sauces with a '
            'depth and intensity that knife-chopped aromatics never achieve.'
        ),
        'body': (
            '## The Technique\n\n'
            '1. Add kosher salt to the mortar first — it acts as an abrasive to break cell walls.\n'
            '2. Add peeled garlic cloves, any tough herb stems, whole toasted spices.\n'
            '3. Pound in a rotating, grinding motion — not just a straight up-and-down — until the aromatics become '
            'a smooth paste.\n'
            "4. Add tender herbs (parsley, cilantro, basil) LAST and bruise gently; don't pulverize or they oxidize.\n\n"
            '## Use Cases\n\n'
            'Chimichurri base, pesto, Thai curry pastes, aioli starter, pasta aglio e olio paste, harissa.'
        ),
        'why_it_works': (
            'Knife cuts shear cells but leave most of them intact — only the cut surfaces release oils. Pounding '
            'crushes cells across the whole piece, releasing every essential oil and blending them into the salt '
            'carrier. The resulting paste has 3-5x more perceived aromatic intensity.'
        ),
        'common_pitfalls': (
            'Using a smooth marble mortar — the tool needs a rough interior (granite, basalt, unglazed ceramic) to '
            "grip. Blenders chop but don't pound; they oxidize and heat the aromatics, producing a harsher flavor."
        ),
        'tags': ['aromatic', 'paste', 'prep', 'chimichurri', 'pesto'],
        'rating': 4,
    },
    {
        'name': 'Chimichurri Compositional Framework',
        'category': 'composition_and_ratio',
        'summary': (
            "Chimichurri is not one sauce — it's a template: fresh herbs + a 3:1 vinaigrette + aromatics + spices. "
            'Swap the herbs (parsley/cilantro/basil/mint), the acid (red wine vinegar/lime/lemon), and the spice '
            '(red pepper flakes/Sichuan peppercorn/sesame) and you have an infinite family of sauces.'
        ),
        'body': (
            '## The Four Components\n\n'
            '1. **Fresh herbs** (packed, roughly chopped): parsley, oregano, cilantro, basil, mint, chives\n'
            '2. **Vinaigrette at 3:1**: olive oil + red wine vinegar (or lemon/lime juice) (see 3:1 Vinaigrette Ratio)\n'
            '3. **Aromatics** (pounded or minced fine): garlic, shallot\n'
            '4. **Spice element**: red pepper flakes, black pepper, smoked paprika, Sichuan peppercorn\n\n'
            '## Four Worked Variations\n\n'
            '- **Classic Argentine**: parsley + oregano + red wine vinegar + garlic + red pepper flakes\n'
            '- **Mexican-inspired**: cilantro + lime + jalapeño + garlic + cumin\n'
            '- **Pasta aglio e olio**: parsley + anchovy + lemon + garlic + red pepper + capers\n'
            '- **Sichuan-inspired**: cilantro + sesame oil + rice vinegar + ginger + Sichuan peppercorn\n\n'
            'All four are the same framework. Learn the template, skip the recipe hunting.'
        ),
        'why_it_works': (
            'Every cuisine has a "green sauce with acid, fat, aromatics, and heat" because the combination hits every '
            'taste receptor (salt, fat, sour, savory, spicy) at once and cuts through rich protein. The framework '
            "survives because it's biologically universal."
        ),
        'common_pitfalls': (
            'Treating it like a recipe instead of a template — chasing the perfect cup-measure of parsley instead of '
            'tasting and adjusting. Also, under-salting; herbs need a lot of salt to sing.'
        ),
        'tags': ['framework', 'sauce', 'herb', 'vinaigrette', 'kwoowk'],
        'rating': 5,
    },
    {
        'name': 'Bloom Whole Spices in Fat',
        'category': 'flavor_development',
        'summary': (
            'Toasting whole or coarsely-cracked spices in hot fat (oil, ghee, butter) for 30-60 seconds before adding '
            'other ingredients releases essential oils that ground pre-toasted spices cannot match. The fat carries '
            'the flavor through the finished dish.'
        ),
        'body': (
            '## The Technique\n\n'
            '1. Heat fat in a pan until shimmering (~325-350°F for most oils).\n'
            '2. Add whole or coarsely-cracked spices (cumin seed, mustard seed, coriander, fennel, black pepper, '
            'cardamom, cloves).\n'
            "3. Watch closely — they'll pop, sputter, and release a wave of aroma within 30-60 seconds.\n"
            '4. The moment they smell toasted (NOT burnt), add your aromatics (onion, garlic, ginger) to stop the '
            'cooking and start the next stage.\n\n'
            '## Use Cases\n\n'
            'Indian curries (tadka/tarka), Moroccan tagines, spice-crusted meats, popcorn seasoning, roast vegetable '
            'finishing oil.'
        ),
        'why_it_works': (
            'Most spice aromatics are fat-soluble, not water-soluble. Dumping dried ground spices into a simmering '
            'liquid dissolves only a fraction of their flavor; toasting in fat dissolves nearly all of it and then '
            'disperses evenly through the dish as the fat coats everything else.'
        ),
        'common_pitfalls': (
            'Going too long — the window between "toasted" and "acrid" is maybe 15 seconds. If you smell sharp/'
            "burnt notes, dump it and start over; you can't rescue burned spice fat."
        ),
        'tags': ['spice', 'bloom', 'tadka', 'fat', 'aromatic-base'],
        'rating': 4,
    },
]


def _ensure_lookup_seeded(session: Session) -> None:
    """Safety net: if Alembic's seed path didn't run, populate the category lookup table."""
    existing = {row[0] for row in session.execute(sqlalchemy.text('SELECT name FROM cooking_technique_categories')).all()}
    for name in COOKING_TECHNIQUE_CATEGORIES:
        if name not in existing:
            session.add(CookingTechniqueCategory(name=name))
    session.flush()


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM cooking_techniques'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    _ensure_lookup_seeded(session)

    techniques: list[CookingTechnique] = []
    seen_slugs: set[str] = set()
    for rep in range(scale):
        for bp in COOKING_TECHNIQUE_BLUEPRINTS:
            name = bp['name'] if scale == 1 else f'{bp["name"]} #{rep + 1}'
            base_slug = slugify(name)
            slug = base_slug
            counter = 2
            while slug in seen_slugs:
                slug = f'{base_slug}-{counter}'
                counter += 1
            seen_slugs.add(slug)
            techniques.append(
                CookingTechnique(
                    name=name,
                    slug=slug,
                    category=bp['category'],
                    summary=bp['summary'],
                    body=bp['body'],
                    why_it_works=bp.get('why_it_works'),
                    common_pitfalls=bp.get('common_pitfalls'),
                    tags=bp.get('tags'),
                    rating=bp.get('rating'),
                )
            )

    session.add_all(techniques)
    session.flush()

    category_counts: dict[str, int] = {}
    for t in techniques:
        category_counts[t.category] = category_counts.get(t.category, 0) + 1
    details = ', '.join(f'{v} {k}' for k, v in sorted(category_counts.items()))

    return SeedResult(model='CookingTechnique', count=len(techniques), details=details)
