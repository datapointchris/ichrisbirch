from ichrisbirch import models

BASE_DATA: list[models.Chat] = [
    models.Chat(
        name='Python Programming',
        category='Technology',
        tags=['Python', 'Programming'],
        messages=[
            models.ChatMessage(
                role="user",
                content="Hello, how can I help you today?",
            ),
            models.ChatMessage(
                role="assistant",
                content="I'd like to know more about Python programming.",
            ),
            models.ChatMessage(
                role="user",
                content="Python is a high-level, interpreted programming language known for its readability and versatility.",
            ),
        ],
    ),
    models.Chat(
        name='Weather Inquiry',
        category='General',
        subcategory='Weather',
        tags=['Weather', 'Information'],
        messages=[
            models.ChatMessage(
                role="user",
                content="What's the weather like today?",
            ),
            models.ChatMessage(
                role="assistant",
                content="I don't have access to real-time weather data. You would need to check a weather service for that information.",
            ),
        ],
    ),
    models.Chat(
        name='Book Recommendations',
        category='Entertainment',
        subcategory='Books',
        tags=['Books', 'Reading'],
        messages=[
            models.ChatMessage(
                role="user",
                content="Can you recommend a good book?",
            ),
            models.ChatMessage(
                role="assistant",
                content="I'd recommend '1984' by George Orwell. It's a classic dystopian novel.",
            ),
            models.ChatMessage(
                role="user",
                content="Thanks for the recommendation!",
            ),
        ],
    ),
]
