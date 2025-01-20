from bs4 import BeautifulSoup


def get_page_data(response):
    status_code = response.status_code
    page = response.text
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.find('title').text if soup.find('title') else ''
    h1 = soup.find('h1').text if soup.find('h1') else ''
    description = soup.find('meta', attrs={'name': 'description'})
    if description:
        description = description['content']
    else:
        description = ''
    return {
        'status_code': status_code,
        'title': title[:255],
        'h1': h1[:255],
        'description': description[:255],
    }
