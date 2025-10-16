import logging

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status
from sqlalchemy import cast
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.exceptions import NotFoundException
from ichrisbirch.config import Settings
from ichrisbirch.config import get_settings
from ichrisbirch.database.session import get_sqlalchemy_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/', response_model=list[schemas.Book], status_code=status.HTTP_200_OK)
async def read_many(search: bool | None = None, session: Session = Depends(get_sqlalchemy_session)):
    query = select(models.Book).order_by(models.Book.priority.asc())

    return list(session.scalars(query).all())


@router.post('/', response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create(book: schemas.BookCreate, session: Session = Depends(get_sqlalchemy_session)):
    obj = models.Book(**book.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.get('/search/', response_model=list[schemas.Book], status_code=status.HTTP_200_OK)
async def search(q: str, session: Session = Depends(get_sqlalchemy_session)):
    """Search for comma-separated list of tags.

    Search terms must be separated and wildcards added.
    `tags` column must be converted from array to string to perform the like comparison for each search term.
    Use the OR to search for any of the specified search terms.
    NOTE: Converting the tags array to text cannot use the GIN index that is set in postgres on the tags column.
    This is a limitation of the array type in that it can't match partial results and use the index.
    """
    logger.debug(f'searching for {q=}')
    search_terms = [f'%{term.strip()}%' for term in q.split(',')]
    logger.debug(f'search terms: {search_terms}')
    title_matches = [models.Book.title.ilike(term) for term in search_terms]
    author_matches = [models.Book.author.ilike(term) for term in search_terms]
    tag_matches = [cast((models.Book.tags), postgresql.TEXT).ilike(term) for term in search_terms]
    all_matches = set(title_matches + author_matches + tag_matches)
    books = select(models.Book).filter(or_(*all_matches)).order_by(models.Book.title.asc())
    logger.debug(books)
    results = session.scalars(books).all()
    logger.debug(f'search found {len(results)} results')
    return list(results)


@router.post('/goodreads/', response_model=schemas.BookGoodreadsInfo, status_code=status.HTTP_201_CREATED)
async def goodreads(request: Request, settings: Settings = Depends(get_settings)):
    """Get book information from Goodreads using the ISBN."""
    request_data = await request.json()
    logger.debug(request_data)
    isbn = request_data.get('isbn')
    url = f'https://www.goodreads.com/search?q={isbn}'
    response = httpx.get(url, follow_redirects=True, headers=settings.mac_safari_request_headers).raise_for_status()
    logger.debug(f'retrieved info from goodreads for isbn: {isbn}')
    # TODO: Fix the typing errors for this POS
    soup = BeautifulSoup(response.content, 'html.parser')
    if title := soup.find('h1', class_='Text Text__title1'):
        title = title.text.strip()  # type: ignore
    else:
        title = 'Not found'  # type: ignore
        logger.error('Title not found')
    if author := soup.find('span', class_='ContributorLink__name'):
        author = author.text.strip()  # type: ignore
    else:
        author = 'Not found'  # type: ignore
        logger.error('Author not found')
    if genre_section := soup.find('div', class_='BookPageMetadataSection__genres'):
        genres = [g.text for g in genre_section.find_all('span', class_='Button__labelItem')][:-1]  # type: ignore
        tags = ', '.join(genres)
    else:
        tags = 'None found'
        logger.error('Genres not found')

    return schemas.BookGoodreadsInfo(title=title, author=author, tags=tags, goodreads_url=str(response.url))


@router.get('/{id}/', response_model=schemas.Book, status_code=status.HTTP_200_OK)
async def read_one(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if book := session.get(models.Book, id):
        return book
    raise NotFoundException('book', id, logger)


@router.get('/isbn/{isbn}/', response_model=schemas.Book | None, status_code=status.HTTP_200_OK)
async def get_book_by_isbn(isbn: str, session: Session = Depends(get_sqlalchemy_session)):
    if book := session.scalar(select(models.Book).where(models.Book.isbn == isbn)):
        return book
    return None  # Do not return an error since this is used for checking for duplicates


@router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, session: Session = Depends(get_sqlalchemy_session)):
    if book := session.get(models.Book, id):
        session.delete(book)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise NotFoundException('book', id, logger)


@router.patch('/{id}/', response_model=schemas.Book, status_code=status.HTTP_200_OK)
async def update(id: int, book_update: schemas.BookUpdate, session: Session = Depends(get_sqlalchemy_session)):
    update_data = book_update.model_dump(exclude_unset=True)
    logger.debug(f'update: book {id} {update_data}')

    if book := session.get(models.Book, id):
        for attr, value in update_data.items():
            setattr(book, attr, value)
        session.commit()
        session.refresh(book)
        return book

    raise NotFoundException('book', id, logger)
