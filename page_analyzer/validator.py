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
        try:
            validation_result = url_validator(url)
        except ValidationError:
            validation_result = False

        if validation_result is not True:
            self.messages['text'] = 'Некорректный URL'
            self.messages['class'] = 'alert-danger'
            return self.messages

        if len(url) > 255:
            self.messages['text'] = "URL превышает 255 символов"
            self.messages['class'] = 'alert-danger'
        else:
            logging.info(f'Start checking URL {url}')
            row = self.url_manager.read_url(url)  # ✅ Читаем URL из БД
            logging.info(f'End checking URL {url}. Result: {row}')
            if row:
                self.messages['text'] = 'Страница уже существует'
                self.messages['class'] = 'alert-info'
                self.messages['id'] = row['id']
            else:
                self.messages['text'] = 'Страница успешно добавлена'
                self.messages['class'] = 'alert-success'

        return self.messages

# Example usage:
# validator = URLValidator("http://example.com")
# result = validator.validate()
