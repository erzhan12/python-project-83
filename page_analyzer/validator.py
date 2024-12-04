from page_analyzer.db import read_url
from validators.url import url as url_validator
from validators import ValidationError
import logging


def validate(url):
    messages = {}

    try:
        validation_result = url_validator(url)
    except ValidationError:
        pass

    # logging.info(validation_result)
    if validation_result is not True:
        messages['text'] = 'Некорректный URL'
        messages['class'] = 'alert-danger'
        return messages

    if len(url) > 255:
        messages['text'] = "URL превышает 255 символов"
        messages['class'] = 'alert-danger'

    else:
        # check DB table if name exists
        logging.info(f'Start reading URL {url}')
        row = read_url(url)
        logging.info(f'End reading URL {url}. Result: {row}')
        if row is not None:
            messages['text'] = 'Страница уже существует'
            messages['class'] = 'alert-info'
            messages['id'] = row['id']

    return messages
