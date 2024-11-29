def validate(url):
    errors = {}
    if not url or not url.startswith('https://') or \
       not url.startswith('http://'):
        errors['message'] = ('Invalid URL. Please provide a valid URL'
                             'starting with http:// or https://')

    if len(url) > 255:
        errors['message'] = "Can't be longer than 255 characters"

    return errors
