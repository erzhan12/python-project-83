# from page_analyzer.db import read_url
from validators.url import url as url_validator
from validators import ValidationError
import logging


class URLValidator:
    """Class to validate URLs."""

    def __init__(self, url_manager):
        self.messages = {}
        self.url_manager = url_manager

    def validate(self, url):
        self.messages = {}
        validation_result = None
        try:
            validation_result = url_validator(url)
        except ValidationError:
            pass

        # logging.info(validation_result)
        if validation_result is not True:
            self.messages['text'] = 'Некорректный URL'
            self.messages['class'] = 'alert-danger'
            return self.messages

        if len(url) > 255:
            self.messages['text'] = "URL превышает 255 символов"
            self.messages['class'] = 'alert-danger'
        else:
            # check DB table if name exists
            logging.info(f'Start reading URL {url}')
            row = self.url_manager.read_url(url)
            logging.info(f'End reading URL {url}. Result: {row}')
            if row is not None:
                self.messages['text'] = 'Страница уже существует'
                self.messages['class'] = 'alert-info'
                self.messages['id'] = row['id']

        return self.messages

# Example usage:
# validator = URLValidator("http://example.com")
# result = validator.validate()
