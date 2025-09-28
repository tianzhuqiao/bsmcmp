import numpy as np
import h5py

from .base import TestBaseAttr


class TestHDF5(TestBaseAttr):
    NAME = 'HDF5'
    EXT = '.h5'

    def get_attrs(self, d):
        return d.attrs

    def get_data(self, d):
        return np.asarray(d)

    def check_group(self, group1, group2, indent=""):

        # check attribute
        match_attr = self.check_attr(group1, group2)

        # check data and its attributes
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
            if isinstance(v, h5py.Group):
                match_data, match_attr = self.check_group(d1, d2, indent + '    ')
            elif isinstance(v, h5py.Dataset):
                if not self.check_data(d1, d2, indent+'    '):
                    match_data = False

                if not self.check_attr(d1, d2, indent+'    '):
                    match_attr = False

            self.end_message_delay()

        for k in group2:
            if k not in group1:
                self.error(k, fg=None)
                self.error(f'{indent}    not found in 1st file')
                match_data = False

        return match_data, match_attr

    def do_test(self, file1, file2):

        f1 = h5py.File(file1)
        f2 = h5py.File(file2)
        match_data, match_attr = self.check_group(f1, f2)
        f1.close()
        f2.close()
        return match_data, match_attr

    def stat_group(self, group1, indent=""):

        # check attribute
        self.stat_attr(group1)

        # check data and its attributes
        for k, v in group1.items():
            self.start_message_delay()

            self.error(k, fg=None)
            if self.has_pattern(k, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                self.end_message_delay()
                continue

            d1 = group1[k]
            if isinstance(v, h5py.Group):
                self.stat_group(d1, indent + '    ')
            elif isinstance(v, h5py.Dataset):
                self.stat_data(d1, indent+'    ')

                self.stat_attr(d1, indent+'    ')

            self.end_message_delay()

    def do_stat(self, file):

        f1 = h5py.File(file)
        self.stat_group(f1)
        f1.close()


@TestHDF5.click_command()
def test_h5(**kwargs):
    TestHDF5.run(**kwargs)
