"""Seed strains across both statuses, with the descriptor vocabularies populated.

Some strains are tried and rated, some are only wanted. A few deliberately carry
almost nothing, because that is what a strain looks like before it has been
tried and often after.
"""

from __future__ import annotations

import random
from typing import Any

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.strain import STRAIN_EFFECTS
from ichrisbirch.models.strain import STRAIN_FLAVORS
from ichrisbirch.models.strain import STRAIN_TERPENES
from ichrisbirch.models.strain import STRAIN_TYPES
from ichrisbirch.models.strain import Strain
from scripts.seed.base import SeedResult
from scripts.seed.base import random_past_date
from scripts.seed.base import random_past_datetime

TRIED: list[dict[str, Any]] = [
    {
        'name': 'Blue Dream',
        'breeder': 'Humboldt Seed Company',
        'lineage': 'Blueberry x Haze',
        'strain_type': 'sativa_dominant',
        'thc_percent': 18.0,
        'cbd_percent': 0.1,
        'rating': 8,
        'effects': ['creative', 'euphoric', 'happy', 'relaxed'],
        'flavors': ['berry', 'sweet', 'earthy'],
        'terpenes': ['myrcene', 'pinene', 'caryophyllene'],
        'source': 'Green Thumb Dispensary',
        'notes': 'The reliable daytime one. Never once made me anxious.',
        'review': 'Does exactly what it says. Would keep in rotation permanently.',
    },
    {
        'name': 'Granddaddy Purple',
        'breeder': 'Ken Estes',
        'lineage': 'Purple Urkle x Big Bud',
        'strain_type': 'indica',
        'thc_percent': 20.5,
        'cbd_percent': 0.1,
        'rating': 9,
        'effects': ['relaxed', 'sleepy', 'happy'],
        'flavors': ['grape', 'berry', 'sweet'],
        'terpenes': ['myrcene', 'caryophyllene', 'linalool'],
        'source': 'Green Thumb Dispensary',
        'notes': 'Genuinely sedating. Not a before-anything strain.',
        'review': 'Best sleep aid I have tried. The grape is not marketing, it is actually there.',
    },
    {
        'name': 'Sour Diesel',
        'breeder': 'Unknown',
        'lineage': 'Chemdawg 91 x Super Skunk',
        'strain_type': 'sativa',
        'thc_percent': 22.0,
        'rating': 6,
        'effects': ['energetic', 'euphoric', 'focused', 'talkative'],
        'flavors': ['diesel', 'citrus', 'skunk'],
        'terpenes': ['limonene', 'caryophyllene', 'myrcene'],
        'source': 'Riverside Cannabis',
        'notes': 'Too much for me above about half a bowl.',
        'review': 'Sharp and fast. Good for a specific mood, not a default.',
    },
    {
        'name': 'Wedding Cake',
        'breeder': 'Seed Junky Genetics',
        'lineage': 'Triangle Kush x Animal Mints',
        'strain_type': 'indica_dominant',
        'thc_percent': 25.0,
        'rating': 8,
        'effects': ['relaxed', 'euphoric', 'hungry'],
        'flavors': ['vanilla', 'sweet', 'earthy'],
        'terpenes': ['limonene', 'caryophyllene', 'myrcene'],
        'source': 'Riverside Cannabis',
        'notes': 'Strong. A little goes a long way.',
    },
    {
        'name': 'Jack Herer',
        'breeder': 'Sensi Seeds',
        'lineage': 'Haze x (Northern Lights #5 x Shiva Skunk)',
        'strain_type': 'sativa_dominant',
        'thc_percent': 19.0,
        'rating': 7,
        'effects': ['creative', 'focused', 'uplifted', 'happy'],
        'flavors': ['pine', 'spicy', 'woody'],
        'terpenes': ['terpinolene', 'pinene', 'caryophyllene'],
        'source': 'Trailhead Provisions',
        'notes': 'Clear-headed. The one that does not interrupt working.',
    },
    {
        'name': 'Northern Lights',
        'breeder': 'Sensi Seeds',
        'lineage': 'Afghani x Thai',
        'strain_type': 'indica',
        'thc_percent': 17.5,
        'rating': 7,
        'effects': ['relaxed', 'sleepy', 'happy'],
        'flavors': ['earthy', 'pine', 'sweet'],
        'terpenes': ['myrcene', 'caryophyllene', 'limonene'],
        'source': 'Trailhead Provisions',
    },
    {
        'name': 'Zkittlez',
        'breeder': '3rd Gen Family',
        'lineage': 'Grape Ape x Grapefruit',
        'strain_type': 'indica_dominant',
        'thc_percent': 19.5,
        'rating': 9,
        'effects': ['happy', 'relaxed', 'euphoric', 'giggly'],
        'flavors': ['tropical', 'berry', 'sweet', 'citrus'],
        'terpenes': ['caryophyllene', 'humulene', 'linalool'],
        'source': 'Green Thumb Dispensary',
        'review': 'The best-tasting thing on this list by a wide margin.',
    },
    {
        'name': 'Durban Poison',
        'breeder': 'Landrace',
        'lineage': 'South African landrace',
        'strain_type': 'sativa',
        'thc_percent': 21.0,
        'rating': 5,
        'effects': ['energetic', 'focused', 'uplifted'],
        'flavors': ['sweet', 'pine', 'spicy'],
        'terpenes': ['terpinolene', 'myrcene', 'ocimene'],
        'source': 'Riverside Cannabis',
        'notes': 'Too racy. Fine in the morning, unusable after noon.',
    },
    {
        'name': 'Charlotte cutting',
        'lineage': 'High-CBD hemp cross',
        'strain_type': 'cbd',
        'thc_percent': 0.5,
        'cbd_percent': 17.0,
        'rating': 6,
        'effects': ['relaxed', 'focused'],
        'flavors': ['earthy', 'pine'],
        'terpenes': ['myrcene', 'pinene', 'bisabolol'],
        'notes': 'No head change at all. Useful, but not for the same reason as the rest.',
    },
]

WANT_TO_TRY: list[dict[str, Any]] = [
    {
        'name': 'Gelato #41',
        'breeder': 'Cookie Fam',
        'lineage': 'Sunset Sherbet x Thin Mint GSC',
        'strain_type': 'hybrid',
        'thc_percent': 24.0,
        'effects': ['euphoric', 'relaxed', 'creative'],
        'flavors': ['sweet', 'berry', 'citrus'],
        'notes': 'Recommended twice now. Find it.',
    },
    {
        'name': 'Purple Punch',
        'breeder': 'Supernova Gardens',
        'lineage': 'Larry OG x Granddaddy Purple',
        'strain_type': 'indica',
        'effects': ['sleepy', 'relaxed'],
        'flavors': ['grape', 'berry', 'vanilla'],
    },
    {
        'name': 'Green Crack',
        'lineage': 'Skunk #1 x Afghani',
        'strain_type': 'sativa',
        'effects': ['energetic', 'focused'],
        'flavors': ['citrus', 'tropical'],
    },
    {
        'name': 'Pineapple Express',
        'lineage': 'Trainwreck x Hawaiian',
        'strain_type': 'sativa_dominant',
        'flavors': ['tropical', 'citrus', 'sweet'],
    },
    # Nothing but a name — the shape a strain has when it is written down off a
    # menu board and looked up later.
    {'name': 'Runtz'},
    {'name': 'MAC 1'},
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM strains'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    strains = []

    for data in TRIED:
        strains.append(
            Strain(
                **data,
                status='tried',
                last_tried_date=random_past_date(400),
                created_at=random_past_datetime(500),
            )
        )

    for data in WANT_TO_TRY:
        strains.append(Strain(**data, status='want_to_try', created_at=random_past_datetime(200)))

    if scale > 1:
        breeders = ['Seed Junky Genetics', 'Cookie Fam', 'Exotic Genetix', 'Compound Genetics', 'Symbiotic Genetics']
        for i in range((scale - 1) * len(TRIED)):
            tried = random.random() > 0.4
            strains.append(
                Strain(
                    name=f'Test Cross #{i + 1}',
                    breeder=random.choice(breeders),
                    strain_type=random.choice(STRAIN_TYPES),
                    status='tried' if tried else 'want_to_try',
                    thc_percent=round(random.uniform(12.0, 30.0), 1),
                    cbd_percent=round(random.uniform(0.0, 2.0), 1),
                    rating=random.randint(1, 10) if tried else None,
                    effects=random.sample(STRAIN_EFFECTS, random.randint(2, 5)),
                    flavors=random.sample(STRAIN_FLAVORS, random.randint(2, 4)),
                    terpenes=random.sample(STRAIN_TERPENES, random.randint(1, 3)),
                    last_tried_date=random_past_date(400) if tried else None,
                    created_at=random_past_datetime(400),
                )
            )

    session.add_all(strains)
    session.flush()

    tried_count = sum(1 for s in strains if s.status == 'tried')
    rated = sum(1 for s in strains if s.rating is not None)
    return SeedResult(
        model='Strain',
        count=len(strains),
        details=f'{tried_count} tried ({rated} rated), {len(strains) - tried_count} want to try',
    )
