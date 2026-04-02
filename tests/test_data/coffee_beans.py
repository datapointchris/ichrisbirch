from ichrisbirch.models.coffee import CoffeeBean

BASE_DATA: list[CoffeeBean] = [
    CoffeeBean(
        name='Ethiopia Yirgacheffe',
        roaster='Ritual Coffee Roasters',
        origin='Ethiopia',
        process='washed',
        roast_level='light',
        brew_method='pour-over',
        flavor_notes='blueberry, jasmine, citrus',
        rating=4.8,
        price=18.50,
        purchase_source='Ritual Coffee direct',
    ),
    CoffeeBean(
        name='Colombia Huila',
        roaster='Blue Bottle Coffee',
        origin='Colombia',
        process='natural',
        roast_level='medium',
        brew_method='espresso',
        flavor_notes='caramel, milk chocolate, cherry',
        rating=4.2,
        price=16.00,
        purchase_source='Blue Bottle subscription',
    ),
    CoffeeBean(
        name='Hair Bender',
        roaster='Stumptown Coffee Roasters',
        origin='Blend',
        process='washed',
        roast_level='medium-dark',
        brew_method='drip',
        flavor_notes='dark chocolate, toffee, dried fruit',
        rating=4.0,
        price=14.00,
    ),
]
