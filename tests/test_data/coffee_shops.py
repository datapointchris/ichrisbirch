from ichrisbirch.models.coffee import CoffeeShop

BASE_DATA: list[CoffeeShop] = [
    CoffeeShop(
        name='Ritual Coffee Roasters',
        address='432B Octavia St',
        city='San Francisco',
        state='CA',
        country='USA',
        google_maps_url='https://maps.google.com/?q=Ritual+Coffee+Roasters+SF',
        rating=4.5,
        notes='Great pour-overs, excellent single-origin selection',
        review='Best espresso in the Mission. The Kenyan single-origin is exceptional.',
    ),
    CoffeeShop(
        name='Blue Bottle Coffee',
        address='300 Webster St',
        city='Oakland',
        state='CA',
        country='USA',
        rating=4.0,
        notes='New Orleans iced coffee is iconic',
    ),
    CoffeeShop(
        name='Stumptown Coffee Roasters',
        address='128 SW 3rd Ave',
        city='Portland',
        state='OR',
        country='USA',
        rating=4.2,
        notes='Hair Bender blend is a classic',
        review='Consistently excellent across all their locations.',
    ),
]
