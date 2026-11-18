from charset_normalizer import detect

def get_file_encoding(filename, default='utf-8'):
    encoding = default
    with open(filename, 'rb') as fp:
        raw = fp.read()
        encoding = detect(raw).get('encoding') or default
    return encoding
