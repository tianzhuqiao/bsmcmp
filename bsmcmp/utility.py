from charset_normalizer import detect

def get_file_encoding(filename, default='utf-8'):
    encoding = default
    with open(filename.strip(), 'rb') as fp:
        raw = fp.read()
        encoding = detect(raw)['encoding']
    return encoding
