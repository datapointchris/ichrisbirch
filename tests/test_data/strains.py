from datetime import date

from ichrisbirch.models import Strain

# Three rows, because ApiCrudTester defaults expected_length=3.
#
# They cover both statuses, both ends of the rating range, and the sparse case:
# 'Runtz' names the array columns nowhere, so it proves the server defaults
# land as [] rather than null in a NOT NULL column.
BASE_DATA: list[Strain] = [
    Strain(
        name='Blue Dream',
        breeder='Humboldt Seed Company',
        lineage='Blueberry x Haze',
        strain_type='sativa_dominant',
        status='tried',
        thc_percent=18.0,
        cbd_percent=0.1,
        rating=8,
        effects=['creative', 'euphoric', 'relaxed'],
        flavors=['berry', 'sweet'],
        terpenes=['myrcene', 'pinene'],
        tags=['daytime'],
        source='Green Thumb Dispensary',
        notes='The reliable daytime one.',
        review='Does exactly what it says.',
        last_tried_date=date(2026, 3, 14),
    ),
    Strain(
        name='Granddaddy Purple',
        breeder='Ken Estes',
        lineage='Purple Urkle x Big Bud',
        strain_type='indica',
        status='tried',
        thc_percent=20.5,
        rating=3,
        effects=['relaxed', 'sleepy'],
        flavors=['grape', 'berry'],
        terpenes=['myrcene', 'linalool'],
        tags=['nighttime'],
        source='Green Thumb Dispensary',
        notes='Genuinely sedating.',
        last_tried_date=date(2026, 1, 9),
    ),
    Strain(
        name='Runtz',
        status='want_to_try',
    ),
]
