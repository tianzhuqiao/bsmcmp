from charset_normalizer import detect

from .base import TestBase

class TestAscii(TestBase):
    NAME = "ascii"
    EXT = '.txt'

    def open_ascii(self, filename):
        encoding = 'utf-8'
        with open(filename.strip(), 'rb') as fp:
            raw = fp.read()
            encoding = detect(raw)['encoding']

        data = None
        with open(filename, 'r', encoding=encoding) as fp:
            data = fp.readlines()
        if data is None:
            self.error(f'Failed to open {filename}')
        return data

    def test(self, file1, file2):
        super().test(file1, file2)

        d1 = self.open_ascii(file1)
        d2 = self.open_ascii(file2)

        match = d1 == d2

        if not match:
            self.mismatch_count += 1
        return match


@TestAscii.click_command()
def test_ascii(**kwargs):
    TestAscii.run(**kwargs)
