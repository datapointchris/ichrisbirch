"""Seed boxes and box items covering all sizes and boolean states."""

from __future__ import annotations

import random

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.box import Box
from ichrisbirch.models.boxitem import BoxItem
from scripts.seed.base import SeedResult

# One box per size to ensure all 9 sizes are represented
BOX_NAMES = [
    ('Kitchen Essentials', 'Medium'),
    ('Books and Media', 'Book'),
    ('Winter Clothes', 'Large'),
    ('Electronics', 'Small'),
    ('Bathroom Supplies', 'Bag'),
    ('Office Supplies', 'Misc'),
    ('Tools and Hardware', 'UhaulSmall'),
    ('Seasonal Decorations', 'Sixteen'),
    ('Computer Monitors', 'Monitor'),
]

ITEMS = [
    'Cast iron skillet',
    'Coffee maker',
    'Cutting board set',
    'Winter jacket',
    'Snow boots',
    'Laptop charger',
    'HDMI cable',
    'Desk lamp',
    'Bath towels',
    'First aid kit',
    'Drill',
    'Hammer',
    'Picture frames',
    'Board games',
    'Yoga mat',
    'Blankets',
    'Spice rack',
    'Blender',
    'Christmas lights',
    'Camping gear',
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM box_packing.items'))
    session.execute(sqlalchemy.text('DELETE FROM box_packing.boxes'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    boxes = []
    for rep in range(scale):
        for i, (name, size) in enumerate(BOX_NAMES):
            box_name = name if scale == 1 else f'{name} #{rep + 1}'
            box_num = i + 1 + rep * len(BOX_NAMES)
            boxes.append(
                Box(
                    number=box_num,
                    name=box_name,
                    size=size,
                    essential=i < 3,
                    warm=i in (2, 7),
                    liquid=i == 4,
                )
            )

    session.add_all(boxes)
    session.flush()

    # Distribute items across boxes
    items = []
    for rep in range(scale):
        for i, item_name in enumerate(ITEMS):
            name = item_name if scale == 1 else f'{item_name} #{rep + 1}'
            # Last 3 items are unboxed (not yet packed)
            box_id = boxes[i % len(boxes)].id if i < len(ITEMS) - 3 else None
            items.append(
                BoxItem(
                    box_id=box_id,
                    name=name,
                    essential=i % 4 == 0,
                    warm=i in (3, 4, 15),
                    liquid=random.random() < 0.1,
                )
            )

    session.add_all(items)
    session.flush()

    return SeedResult(
        model='Box',
        count=len(boxes) + len(items),
        details=f'{len(boxes)} boxes, {len(items)} items',
    )
