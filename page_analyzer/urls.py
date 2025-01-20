from urllib.parse import urlparse

from validators.url import url as url_validator


def validate(url):
    if not url:
        return 'URL обязателен'
    elif not url_validator(url):
        return 'Некорректный URL'
    elif len(url) > 255:
        return 'URL превышает 255 символов'


def normalize(url):
    out = urlparse(url)
    scheme = out.scheme.lower()
    netloc = out.netloc.lower()
    return f'{scheme}://{netloc}'
