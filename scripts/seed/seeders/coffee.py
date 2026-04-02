"""Seed coffee shops and coffee beans with realistic development data.

Shops are seeded first; some beans are linked to shops via FK, others have a
free-text purchase_source, and some have neither (impulse buys with no record).
"""

from __future__ import annotations

import random

import sqlalchemy
from sqlalchemy.orm import Session

from ichrisbirch.models.coffee import CoffeeBean
from ichrisbirch.models.coffee import CoffeeShop
from scripts.seed.base import SeedResult
from scripts.seed.base import random_past_datetime

SHOPS = [
    {
        'name': 'Ritual Coffee Roasters',
        'address': '432B Octavia St',
        'city': 'San Francisco',
        'state': 'CA',
        'country': 'USA',
        'google_maps_url': 'https://maps.google.com/?q=Ritual+Coffee+Roasters+SF',
        'website': 'https://ritualroasters.com',
        'rating': 4.5,
        'notes': 'Exceptional single-origin espresso program. The Valencia St location is the best.',
        'review': 'Best espresso in the Mission. Kenyan single-origin always on rotation.',
    },
    {
        'name': 'Blue Bottle Coffee',
        'address': '300 Webster St',
        'city': 'Oakland',
        'state': 'CA',
        'country': 'USA',
        'website': 'https://bluebottlecoffee.com',
        'rating': 4.0,
        'notes': 'New Orleans iced coffee is iconic. Consistent across all locations.',
    },
    {
        'name': 'Stumptown Coffee Roasters',
        'address': '128 SW 3rd Ave',
        'city': 'Portland',
        'state': 'OR',
        'country': 'USA',
        'website': 'https://stumptowncoffee.com',
        'rating': 4.2,
        'notes': 'Hair Bender blend is a classic. Portland flagship is worth a visit.',
        'review': 'Consistently excellent. Hair Bender is one of the great house blends.',
    },
    {
        'name': 'Counter Culture Coffee',
        'address': '905 Kezar Dr',
        'city': 'San Francisco',
        'state': 'CA',
        'country': 'USA',
        'rating': 4.3,
        'notes': 'Training center vibes. Staff very knowledgeable about origin and process.',
    },
    {
        'name': 'Intelligentsia Coffee',
        'address': '3123 Glendale Blvd',
        'city': 'Los Angeles',
        'state': 'CA',
        'country': 'USA',
        'website': 'https://intelligentsiacoffee.com',
        'rating': 4.4,
        'notes': 'Direct trade pioneers. Black Cat espresso is benchmark quality.',
        'review': 'One of the founding pillars of third-wave coffee. Never disappoints.',
    },
    {
        'name': 'George Howell Coffee',
        'address': '505 Washington St',
        'city': 'Boston',
        'state': 'MA',
        'country': 'USA',
        'rating': 4.6,
        'notes': 'Arguably the best in Boston. George Howell is a legend in specialty coffee.',
        'review': 'Terroir series is stunning. Every cup is precisely dialed in.',
    },
]

BEANS = [
    {
        'name': 'Ethiopia Yirgacheffe',
        'roaster': 'Ritual Coffee Roasters',
        'origin': 'Ethiopia',
        'process': 'washed',
        'roast_level': 'light',
        'brew_method': 'pour-over',
        'flavor_notes': 'blueberry, jasmine, citrus, bergamot',
        'rating': 4.8,
        'price': 18.50,
        'purchase_source': 'Ritual Coffee direct',
    },
    {
        'name': 'Colombia Huila',
        'roaster': 'Blue Bottle Coffee',
        'origin': 'Colombia',
        'process': 'natural',
        'roast_level': 'medium',
        'brew_method': 'espresso',
        'flavor_notes': 'caramel, milk chocolate, cherry, hazelnut',
        'rating': 4.2,
        'price': 16.00,
        'purchase_source': 'Blue Bottle subscription',
    },
    {
        'name': 'Hair Bender',
        'roaster': 'Stumptown Coffee Roasters',
        'origin': 'Blend (Ethiopia, Indonesia, Latin America)',
        'process': 'washed',
        'roast_level': 'medium-dark',
        'brew_method': 'drip',
        'flavor_notes': 'dark chocolate, toffee, dried fruit, orange zest',
        'rating': 4.0,
        'price': 14.00,
        'review': 'My go-to house blend for years. Reliable and complex.',
    },
    {
        'name': 'Guatemala Antigua',
        'roaster': 'Counter Culture Coffee',
        'origin': 'Guatemala',
        'process': 'washed',
        'roast_level': 'medium',
        'brew_method': 'aeropress',
        'flavor_notes': 'brown sugar, almond, lime, honey',
        'rating': 4.1,
        'price': 15.50,
        'purchase_source': 'Counter Culture direct mail',
    },
    {
        'name': 'Black Cat Classic Espresso',
        'roaster': 'Intelligentsia Coffee',
        'origin': 'Blend',
        'process': 'washed',
        'roast_level': 'medium',
        'brew_method': 'espresso',
        'flavor_notes': 'milk chocolate, dried cherry, vanilla, cola',
        'rating': 4.7,
        'price': 17.00,
        'review': 'Benchmark espresso blend. Forgiving to dial in, exceptional when right.',
    },
    {
        'name': 'Kenya Kiambu AA',
        'roaster': 'George Howell Coffee',
        'origin': 'Kenya',
        'process': 'washed',
        'roast_level': 'light',
        'brew_method': 'pour-over',
        'flavor_notes': 'blackcurrant, tomato, grapefruit, brown sugar',
        'rating': 4.9,
        'price': 22.00,
        'review': 'One of the finest Kenyas I have had. The blackcurrant note is extraordinary.',
    },
    {
        'name': 'Sumatra Mandheling',
        'roaster': 'Stumptown Coffee Roasters',
        'origin': 'Indonesia',
        'process': 'wet-hulled',
        'roast_level': 'dark',
        'brew_method': 'french-press',
        'flavor_notes': 'cedar, dark chocolate, earth, dried herbs',
        'rating': 3.8,
        'price': 13.50,
        'notes': 'Polarizing but fascinating. The wet-hull process creates something unlike anything else.',
    },
    {
        'name': 'Panama Geisha',
        'roaster': 'Counter Culture Coffee',
        'origin': 'Panama',
        'process': 'natural',
        'roast_level': 'light',
        'brew_method': 'pour-over',
        'flavor_notes': 'peach, jasmine, mango, white tea',
        'rating': 5.0,
        'price': 42.00,
        'review': 'Transcendent. The best single cup of coffee I have ever had.',
        'notes': 'Limited release, grabbed two bags. Worth every penny.',
    },
    {
        'name': 'Brazil Fazenda Santa Inês',
        'roaster': 'Intelligentsia Coffee',
        'origin': 'Brazil',
        'process': 'natural',
        'roast_level': 'medium',
        'brew_method': 'drip',
        'flavor_notes': 'peanut butter, caramel, milk chocolate, red apple',
        'rating': 4.3,
        'price': 15.00,
        'purchase_source': 'Trade Coffee subscription',
    },
    {
        'name': 'Costa Rica Tarrazu',
        'roaster': 'Verve Coffee Roasters',
        'origin': 'Costa Rica',
        'process': 'honey',
        'roast_level': 'medium-light',
        'brew_method': 'aeropress',
        'flavor_notes': 'peach, honey, brown sugar, almond',
        'rating': 4.4,
        'price': 16.50,
        'purchase_source': 'Verve website',
    },
    {
        'name': 'Ethiopia Bench Maji',
        'roaster': 'George Howell Coffee',
        'origin': 'Ethiopia',
        'process': 'natural',
        'roast_level': 'light',
        'brew_method': 'pour-over',
        'flavor_notes': 'strawberry, watermelon, rose, hibiscus',
        'rating': 4.6,
        'price': 20.00,
        'notes': 'Natural Ethiopian coffees are in a category of their own.',
    },
    {
        'name': 'Cold Brew Concentrate',
        'roaster': 'Blue Bottle Coffee',
        'origin': 'Blend',
        'process': 'washed',
        'roast_level': 'medium-dark',
        'brew_method': 'cold-brew',
        'flavor_notes': 'dark chocolate, molasses, brown sugar',
        'rating': 3.9,
        'price': 12.00,
        'purchase_source': 'Blue Bottle retail store',
        'notes': 'Convenient for summer. Dilute 1:1 with water or milk.',
    },
]


def clear(session: Session) -> None:
    session.execute(sqlalchemy.text('DELETE FROM coffee.coffee_beans'))
    session.execute(sqlalchemy.text('DELETE FROM coffee.coffee_shops'))


def seed(session: Session, scale: int = 1) -> SeedResult:
    shops = []
    for shop_data in SHOPS:
        shop = CoffeeShop(
            **shop_data,
            date_visited=random_past_datetime(730) if random.random() > 0.2 else None,
            created_at=random_past_datetime(365),
        )
        shops.append(shop)
    session.add_all(shops)
    session.flush()  # get IDs before inserting beans

    shop_by_name = {s.name: s for s in shops}

    beans = []
    for bean_data in BEANS:
        data = bean_data.copy()
        roaster = data.get('roaster', '')
        if roaster in shop_by_name and 'purchase_source' not in data:
            data['coffee_shop_id'] = shop_by_name[roaster].id
        data['purchase_date'] = random_past_datetime(365) if random.random() > 0.3 else None
        data['created_at'] = random_past_datetime(365)
        beans.append(CoffeeBean(**data))

    if scale > 1:
        extra_roasters = ['Onyx Coffee Lab', 'La Cabra', 'Passenger Coffee', 'Heart Roasters', 'Equator Coffees']
        extra_origins = ['Honduras', 'El Salvador', 'Rwanda', 'Burundi', 'Peru', 'Yemen']
        extra_processes = ['washed', 'natural', 'honey', 'anaerobic']
        extra_roasts = ['light', 'medium-light', 'medium', 'medium-dark', 'dark']
        extra_methods = ['pour-over', 'espresso', 'french-press', 'aeropress', 'cold-brew', 'drip', 'moka-pot']
        for i in range((scale - 1) * len(BEANS)):
            beans.append(
                CoffeeBean(
                    name=f'Single Origin #{i + 1}',
                    roaster=random.choice(extra_roasters),
                    origin=random.choice(extra_origins),
                    process=random.choice(extra_processes),
                    roast_level=random.choice(extra_roasts),
                    brew_method=random.choice(extra_methods),
                    rating=round(random.uniform(3.0, 5.0), 1),
                    price=round(random.uniform(12.0, 28.0), 2),
                    purchase_date=random_past_datetime(365),
                    created_at=random_past_datetime(365),
                )
            )

    session.add_all(beans)
    session.flush()

    beans_with_shop = sum(1 for b in beans if b.coffee_shop_id is not None)
    beans_with_source = sum(1 for b in beans if b.purchase_source is not None)
    return SeedResult(
        model='CoffeeShop+CoffeeBean',
        count=len(shops) + len(beans),
        details=f'{len(shops)} shops, {len(beans)} beans ({beans_with_shop} linked to shop, {beans_with_source} with text source)',
    )
