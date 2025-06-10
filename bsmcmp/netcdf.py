import numpy as np
import netCDF4
from netCDF4 import Dataset

from .base import TestBaseAttr

class TestNetcdf(TestBaseAttr):
    NAME = 'netCDF'
    EXT = '.nc'

    def get_attrs(self, d):
        attrs = {}
        for att in d.ncattrs():
            attrs[att] = d.getncattr(att)
        return attrs

    def get_data(self, d):
        return np.asarray(d[:])

    def check_group(self, group1, group2, indent=""):

        # check attribute
        match_attr = self.check_attr(group1, group2)

        # check data and its attributes
        match_data = True
        match_data = len(group1.variables) == len(group2.variables)
        for k in group1.variables:
            self.echo(k)
            if self.has_pattern(k, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                continue

            if k not in group2.variables:
                self.error(f'group "{k}" not found in 2nd file')
                match_data = False
                continue

            d1 = group1.variables[k]
            d2 = group2.variables[k]
            if not self.check_attr(d1, d2, indent+'    '):
                match_attr = False
            if not self.check_data(d1, d2, indent+'    '):
                match_data = False

        # check subgroups
        if len(group1.groups) != len(group2.groups):
            match_data = False
        for k, g in group1.groups.items():
            if k not in group2.groups:
                match_data = False
                self.error(f"{k} not found in 2nd file", bg='red')
            group_data, group_attr = self.check_group(g, group2[k], indent+'    ')
            match_data = match_data and group_data
            match_attr = match_data and group_attr

        return match_data, match_attr

    def do_test(self, file1, file2):
        nc_p = Dataset(file1)
        nc_m = Dataset(file2)
        match_data, match_attr = self.check_group(nc_p, nc_m)
        nc_p.close()
        nc_m.close()
        return match_data, match_attr


@TestNetcdf.click_command()
def test_netcdf(**kwargs):
    TestNetcdf.run(**kwargs)
