import requests
from bs4 import BeautifulSoup


class URLChecker:

    def check(self, url):
        # try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        # except requests.exceptions.RequestException as e:
        #     return {'error': str(e)}

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the title
        page_title = soup.title.string if soup.title else ''

        # Extract the description
        description_meta = soup.find('meta', attrs={'name': 'description'})
        if description_meta:
            page_description = description_meta['content']
        else:
            page_description = ''

        # Extract the first h1 tag
        h1_tag = soup.find('h1')
        page_h1 = h1_tag.string if h1_tag else ''
        # return {
        #     'status_code': response.status_code,
        #     'h1': page_h1,
        #     'title': page_title,
        #     'description': page_description
        # }
        return (
            response.status_code,
            page_h1,
            page_title,
            page_description
        )
