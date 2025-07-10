import numpy as np
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import xarray as xr

from .base import TestBaseAttr


class TestGRIB2(TestBaseAttr):
    NAME = 'grib'
    EXT = '.grib2'

    def get_attrs(self, d):
        return d.attrs

    def get_data(self, d):
        return d.to_numpy()

    def check_group(self, group1, group2, indent=""):

        # check attribute
        match_attr = self.check_attr(group1, group2)

        # check data and its attributes
        match_data = True
        match_data = len(group1) == len(group2)
        for k in group1.variables:
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
            if not self.check_data(d1, d2, indent+'    '):
                match_data = False

            if not self.check_attr(d1, d2, indent+'    '):
                match_attr = False

            self.end_message_delay()

        for k in group2.variables:
            if k not in group1:
                self.error(k, fg=None)
                self.error(f'{indent}    not found in 1st file')
                match_data = False

        return match_data, match_attr

    def do_test(self, file1, file2):

        f1 = xr.open_dataset(file1)
        f2 = xr.open_dataset(file2)
        match_data, match_attr = self.check_group(f1, f2)
        f1.close()
        f2.close()
        return match_data, match_attr

@TestGRIB2.click_command()
def test_grib2(**kwargs):
    TestGRIB2.run(**kwargs)
