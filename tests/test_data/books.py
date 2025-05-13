from ichrisbirch.models import Book

BASE_DATA: list[Book] = [
    Book(
        isbn="9780451524935",
        title="1984",
        author="George Orwell",
        tags=["Dystopian", "Classic", "Political"],
        goodreads_url="https://www.goodreads.com/book/show/40961427-1984",
        priority=1,
        rating=5,
        location="Bookshelf",
        notes="A classic dystopian novel",
    ),
    Book(
        isbn="9780060935467",
        title="To Kill a Mockingbird",
        author="Harper Lee",
        tags=["Classic", "Fiction", "Coming-of-age"],
        goodreads_url="https://www.goodreads.com/book/show/2657.To_Kill_a_Mockingbird",
        priority=2,
        rating=4,
        location="Bookshelf",
        notes="Pulitzer Prize winner",
    ),
    Book(
        isbn="9780547928227",
        title="The Hobbit",
        author="J.R.R. Tolkien",
        tags=["Fantasy", "Adventure", "Classic"],
        goodreads_url="https://www.goodreads.com/book/show/5907.The_Hobbit",
        priority=3,
        rating=5,
        location="Bookshelf",
        notes="Prequel to Lord of the Rings",
    ),
]