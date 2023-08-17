from models.model import ShortURL
from schemas.model import ShortURLCreate
from .base import RepositoryDB


class RepositoryShortUrl(RepositoryDB[ShortURL, ShortURLCreate]):
    pass


url_crud = RepositoryShortUrl(ShortURL)
