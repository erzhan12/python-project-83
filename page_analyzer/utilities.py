import validators
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def validate_url(url):
    errors = {}
    if not validators.url(url):
        errors["url"] = "This is not URL!"
    if url == '':
        errors["url"] = "URL не должен быть пустым"
    if len(url) >= 255:
        errors["url"] = "URL должен быть короче 255 символов"
    return errors


def parse_url(url):
    parced_url = urlparse(url)
    normalized_url = '://'.join(
        [parced_url.scheme, parced_url.netloc]
    ) if parced_url.scheme else ''
    return normalized_url


def parse_response(response):
    soup = BeautifulSoup(response.text, 'lxml')
    description_tag = soup.find("meta", attrs={"name": "description"})
    return {
        'h1': soup.h1.string if soup.h1 else None,
        'title': soup.title.string if soup.title else None,
        'description': description_tag.get(
            'content'
        ) if description_tag else None
    }
