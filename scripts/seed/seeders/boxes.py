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
    'Mixing bowls',
    'Spatula set',
    'Winter jacket',
    'Snow boots',
    'Fleece blanket',
    'Wool scarf',
    'Laptop charger',
    'HDMI cable',
    'USB hub',
    'Power strip',
    'Desk lamp',
    'Bath towels',
    'First aid kit',
    'Shampoo bottles',
    'Drill',
    'Hammer',
    'Screwdriver set',
    'Tape measure',
    'Picture frames',
    'Board games',
    'Playing cards',
    'Yoga mat',
    'Blankets',
    'Throw pillows',
    'Spice rack',
    'Blender',
    'Can opener',
    'Christmas lights',
    'Ornament box',
    'Wreath',
    'Camping gear',
    'Sleeping bag',
    'Headlamp',
]

# Target item counts per box index — creates variety: empty, light, and heavy boxes
# Must have len(BOX_NAMES) entries. None means unboxed items draw from that slot.
ITEMS_PER_BOX = [5, 2, 7, 1, 0, 3, 8, 1, 4]


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

    # Distribute items across boxes with varied counts
    items = []
    for rep in range(scale):
        item_pool = ITEMS.copy()
        random.shuffle(item_pool)
        pool_idx = 0

        for box_idx, count in enumerate(ITEMS_PER_BOX):
            box = boxes[box_idx + rep * len(BOX_NAMES)]
            for _ in range(count):
                if pool_idx >= len(item_pool):
                    break
                item_name = item_pool[pool_idx]
                name = item_name if scale == 1 else f'{item_name} #{rep + 1}'
                items.append(
                    BoxItem(
                        box_id=box.id,
                        name=name,
                        essential=pool_idx % 4 == 0,
                        warm=pool_idx % 7 == 0,
                        liquid=random.random() < 0.1,
                    )
                )
                pool_idx += 1

        # Remaining items are unboxed (not yet packed)
        while pool_idx < len(item_pool):
            item_name = item_pool[pool_idx]
            name = item_name if scale == 1 else f'{item_name} #{rep + 1}'
            items.append(
                BoxItem(
                    box_id=None,
                    name=name,
                    essential=pool_idx % 4 == 0,
                    warm=pool_idx % 7 == 0,
                    liquid=random.random() < 0.1,
                )
            )
            pool_idx += 1

    session.add_all(items)
    session.flush()

    return SeedResult(
        model='Box',
        count=len(boxes) + len(items),
        details=f'{len(boxes)} boxes, {len(items)} items',
    )
