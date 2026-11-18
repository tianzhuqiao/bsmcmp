from .base import TestBase
from .utility import get_file_encoding

class TestAscii(TestBase):
    NAME = "ascii"
    EXT = '.txt'

    def open_ascii(self, filename):
        encoding = get_file_encoding(filename)

        data = None
        with open(filename, 'r', encoding=encoding) as fp:
            data = fp.readlines()
        if data is None:
            self.error(f'Failed to open {filename}')
        return data

    def do_test(self, file1, file2):
        import difflib

        d1 = self.open_ascii(file1)
        d2 = self.open_ascii(file2)

        match = d1 == d2

        if not match:
            for line in difflib.ndiff(d1, d2):
                self.error(line, nl=False, fg=None)

        return match


@TestAscii.click_command()
def test_ascii(**kwargs):
    TestAscii.run(**kwargs)
