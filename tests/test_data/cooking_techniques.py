from ichrisbirch.models import CookingTechnique

# Category lookup table is populated by the initial migration — no need to insert it here.

BASE_DATA: list[CookingTechnique] = [
    CookingTechnique(
        name='Test Vinaigrette Ratio',
        slug='test-vinaigrette-ratio',
        category='composition_and_ratio',
        summary='3:1 oil to acid.',
        body='3 parts fat to 1 part acid, with mustard to emulsify.',
        why_it_works='Balance of fat and acidity matches taste receptors.',
        common_pitfalls='Adding oil too fast breaks the emulsion.',
        tags=['sauce', 'framework'],
        rating=5,
    ),
    CookingTechnique(
        name='Test Caramelize Paste',
        slug='test-caramelize-paste',
        category='flavor_development',
        summary='Fry tomato paste before adding liquid.',
        body='Smear tomato paste on hot pan for 2-3 minutes until brick red.',
        why_it_works='Maillard reaction on concentrated sugars/amino acids.',
        common_pitfalls='Burning past brick-red produces acrid flavor.',
        tags=['maillard', 'stew'],
        rating=4,
    ),
    CookingTechnique(
        name='Test Bean Soak',
        slug='test-bean-soak',
        category='preservation_and_pre_treatment',
        summary='24-hour salted soak.',
        body='Soak dried beans in salted water 12-24 hours, discarding the water.',
        why_it_works='Reduces phytic acid, oligosaccharides, and lectins.',
        common_pitfalls='Cooking in the soaking water defeats the purpose.',
        tags=['beans', 'soak'],
        rating=None,
    ),
]
