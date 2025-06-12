from collections.abc import MutableMapping
from csv import Sniffer
import numpy as np
import pandas as pd

from .base import TestBaseGroup
from .utility import get_file_encoding


class TestCSV(TestBaseGroup):
    NAME = 'csv'
    EXT = '.csv'

    def get_data(self, d):
        return np.asarray(d)

    def check_group(self, group1, group2, indent=""):

        # check data
        match_data = True
        match_data = len(group1) == len(group2)

        for k, v in group1.items():
            self.start_message_delay()

            self.error(k, fg=None)
            if self.has_pattern(k, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                continue

            if k not in group2:
                self.error(f'group "{k}" not found in 2nd file')
                match_data = False
                continue

            d1 = group1[k]
            d2 = group2[k]
            if isinstance(v, MutableMapping):
                match_data = self.check_group(d1, d2, indent + '    ')
            else:
                if not self.check_data(d1, d2, indent+'    '):
                    match_data = False

            self.end_message_delay()

        return match_data

    def do_test(self, file1, file2):
        def _load(filename):
            encoding = get_file_encoding(filename)

            sep = ','
            with open(filename, encoding=encoding) as fp:
                line = fp.readline()
                s = Sniffer()
                d = s.sniff(line)
                sep = d.delimiter
            csv = pd.read_csv(filename, sep=sep)
            return csv

        f1 = _load(file1)
        f2 = _load(file2)
        if f1 is not None or f2 is not None:
            match_data = self.check_group(f1, f2)
        else:
            match_data = False
        return match_data

@TestCSV.click_command()
def test_csv(**kwargs):
    TestCSV.run(**kwargs)
