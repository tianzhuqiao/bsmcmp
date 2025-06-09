import numpy as np
import netCDF4
from netCDF4 import Dataset
import click

from .base import TestBase, common_options

class TestNetcdf(TestBase):
    NAME = 'netcdf'
    def __init__(self):
        super().__init__()
        self.ext = ".nc"
        self.mismatch_attr = 0
        self.stop_on_attr_mismatch = False
        self.ignore_variables = []
        self.ignore_attributes = []

    def check_attr(self, d1, d2, indent=''):
        match = True
        if sorted(d1.ncattrs()) != sorted(d2.ncattrs()):
            self.error(f"{indent}different attributes")
            self.echo(f"{indent}    {sorted(d1.ncattrs())}")
            self.echo(f"{indent}    {sorted(d2.ncattrs())}")

        for att in d1.ncattrs():
            if att not in d2.ncattrs():
                continue
            if self.has_pattern(att, self.ignore_attributes):
                self.warning(f"{indent}{att}: ignore")
                continue
            if d1.getncattr(att) != d2.getncattr(att):
                match = False
                self.error(f"{indent}{att}: fail")
                self.echo(f"{indent}    {d1.getncattr(att)}")
                self.echo(f"{indent}    {d2.getncattr(att)}")
            else:
                self.success(f"{indent}{att}: pass")
        return match

    def check_data(self, d1, d2, indent=''):
        d1 = np.asarray(d1[:])
        d2 = np.asarray(d2[:])
        match = True
        if d1.shape == d2.shape:
            if not d1.shape:
                # empty variable
                match = True
            else:
                match = np.array_equal(d1, d2, equal_nan=True)
        else:
            match = False

        if not match:
            self.error(f"{indent}data: fail")
            err = np.abs(d1[:]-d2[:])
            w = np.argwhere(err == np.max(err))
            n_zero_err = np.sum((err.flatten() == 0))
            n_all = len(err.flatten())

            self.error(f"{indent}       max error: {np.nanmax(err)} at {np.argwhere(err == np.max(err))}")
            self.error(f"{indent}              d1: {d1[:][tuple(w[0])]}")
            self.error(f"{indent}              d2: {d2[:][tuple(w[0])]}")
            self.error(f"{indent}       avg error: {np.nanmean(err)}")
            self.error(f"{indent}       std error: {np.nanstd(err)}")
            self.error(f"{indent}      0 error(%): {n_zero_err}/{n_all} = {n_zero_err/n_all}")

        else:
            self.success(f"{indent}data: pass")

        return match

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

        # check groups
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

    def test(self, file1, file2):
        super().test(file1, file2)

        nc_p = Dataset(file1)
        nc_m = Dataset(file2)
        match_data, match_attr = self.check_group(nc_p, nc_m)
        nc_p.close()
        nc_m.close()
        if not match_data:
            self.mismatch_count += 1

        if not match_attr:
            self.mismatch_attr += 1
        if self.stop_on_attr_mismatch and not match_attr:
            self._stop = True
            self.error("attribute mismatch")

        if self.stop_on_mismatch and not match_data:
            self._stop = True
            self.error("data mismatch")

        self.echo("--------")
        self.echo("overall:")
        if match_data:
            self.success('    data: pass')
        else:
            self.error('    data: fail')
        if match_attr:
            self.success('    attribute: pass')
        else:
            self.error('    attribute: fail')
        return match_data

    def test_all(self, folder1, folder2):
        if super().test_all(folder1, folder2):
            self.echo(f'    attr mismatch: {self.mismatch_attr}', verbose=True)

    def load_config(self, **kwargs):
        kwargs = super().load_config(**kwargs)
        self.stop_on_attr_mismatch = kwargs.get('stop_on_attr_mismatch', self.stop_on_attr_mismatch)
        self.ignore_variables = kwargs.get('ignore_var', [])
        self.ignore_attributes = kwargs.get('ignore_att', [])
        return kwargs


@click.command('netcdf', context_settings={'show_default': True})
@common_options('.nc', 'netCDF')
@click.option('--stop_on_attr_mismatch', is_flag=True, default=False, help='Stop when see any attribute mismatch')
@click.option('--ignore_var', multiple=True, help='variables to be ignored')
@click.option('--ignore_att', multiple=True, help='attributes to be ignored')
def test_netcdf(**kwargs):
    test = TestNetcdf()
    kwargs = test.load_config(**kwargs)
    if kwargs['file1'] is not None and kwargs['file2'] is not None:
        test.stop_on_mismatch = False
        test.stop_on_attr_mismatch = False
        test.verbose = True
        test.test(kwargs['file1'], kwargs['file2'])
        test.show_result()
        return
    if kwargs['folder1'] is not None and kwargs['folder2'] is not None:
        test.verbose = False
        test.test_all(kwargs['folder1'], kwargs['folder2'])
