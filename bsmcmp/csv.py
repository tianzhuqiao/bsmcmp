from collections.abc import MutableMapping
import numpy as np

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
                self.end_message_delay()
                continue

            if k not in group2:
                self.error(f'{indent}    not found in 2nd file')
                match_data = False
                self.end_message_delay()
                continue

            d1 = group1[k]
            d2 = group2[k]
            if isinstance(v, MutableMapping):
                group_match_data = self.check_group(d1, d2, indent + '    ')
                match_data = match_data and group_match_data
            else:
                if not self.check_data(d1, d2, indent+'    '):
                    match_data = False

            self.end_message_delay()

        for k in group2:
            if k not in group1:
                self.error(k, fg=None)
                self.error(f'{indent}    not found in 1st file')
                match_data = False


        return match_data

    def _load(self, filename):
        from csv import Sniffer
        import pandas as pd

        encoding = get_file_encoding(filename)
        sep = ','
        with open(filename, encoding=encoding) as fp:
            line = fp.readline()
            try:
                s = Sniffer()
                d = s.sniff(line)
                sep = d.delimiter
            except:
                sep = ','
        csv = pd.read_csv(filename, sep=sep)
        return csv

    def do_test(self, file1, file2):
        f1 = self._load(file1)
        f2 = self._load(file2)
        if f1 is not None and f2 is not None:
            match_data = self.check_group(f1, f2)
        else:
            match_data = False
        return match_data

    def stat_group(self, group1, indent=""):

        # check data
        for k, v in group1.items():
            self.start_message_delay()

            self.error(k, fg=None)
            if self.has_pattern(k, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                self.end_message_delay()
                continue

            d1 = group1[k]
            if isinstance(v, MutableMapping):
                self.stat_group(d1, indent + '    ')
            else:
                self.stat_data(d1, indent+'    ')

            self.end_message_delay()


    def do_stat(self, file):
        f1 = self._load(file)
        if f1 is not None:
            self.stat_group(f1)


@TestCSV.click_command()
def test_csv(**kwargs):
    TestCSV.run(**kwargs)
