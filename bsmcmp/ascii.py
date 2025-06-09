import click
from charset_normalizer import detect

from .base import TestBase, common_options

class TestAscii(TestBase):
    NAME = "ascii"
    def __init__(self):
        super().__init__()
        self.ext = ".asc"

    def open_ascii(self, filename):
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


@click.command('ascii', context_settings={'show_default': True})
@common_options('.asc', 'ASCII')
def test_ascii(**kwargs):
    test = TestAscii()
    kwargs = test.load_config(**kwargs)
    if kwargs['file1'] is not None and kwargs['file2'] is not None:
        test.stop_on_mismatch = False
        test.verbose = True
        test.test(kwargs['file1'], kwargs['file2'])
        test.show_result()
        return
    if kwargs['folder1'] is not None and kwargs['folder2'] is not None:
        test.verbose = False
        test.test_all(kwargs['folder1'], kwargs['folder2'])
