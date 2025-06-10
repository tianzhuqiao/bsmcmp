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
            self.echo(k)
            if self.has_pattern(k, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                continue

            if k not in group2:
                self.error(f'group "{k}" not found in 2nd file')
                match_data = False
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

        return match_data, match_attr

    def do_test(self, file1, file2):

        f1 = h5py.File(file1)
        f2 = h5py.File(file2)
        match_data, match_attr = self.check_group(f1, f2)
        f1.close()
        f2.close()
        return match_data, match_attr

@TestHDF5.click_command()
def test_h5(**kwargs):
    TestHDF5.run(**kwargs)
