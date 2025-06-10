from collections.abc import MutableMapping
import numpy as np
from scipy import io
import h5py

from .base import TestBaseGroup


class TestMat(TestBaseGroup):
    NAME = 'matlab'
    EXT = '.mat'

    def get_data(self, d):
        return np.asarray(d)

    def process_record(self, d):
        if hasattr(d, 'keys'):
            keys = [k for k in d.keys() if not k.startswith('__')]
            data = {}
            for k in keys:
                data[k] = self.process_record(d[k])
            return data

        if not hasattr(d, 'dtype'):
            return d

        if d.dtype.names is None:
            if len(d) == 1 and d.dtype.name == 'object':
                return self.process_record(d[0])
            if hasattr(d, 'shape'):
                if len(d.shape) <= 1 or sorted(d.shape)[-2] == 1:
                    d = np.array(d).flatten()
            return d
        data = {}
        for name in d.dtype.names:
            data[name] = self.process_record(d[name])
        return data

    def check_group(self, group1, group2, indent=""):

        # check data
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
            if isinstance(v, MutableMapping):
                match_data = self.check_group(d1, d2, indent + '    ')
            else:
                if not self.check_data(d1, d2, indent+'    '):
                    match_data = False

        return match_data

    def do_test(self, file1, file2):
        def _load(filename):
            raw = None
            try:
                try:
                    raw = io.loadmat(filename)
                except:
                    raw = h5py.File(filename,'r')
            except:
                pass
            if raw is None:
                self.error(f"failed to open {filename}")
            return raw

        def _close(fp):
            if isinstance(fp, h5py.File):
                fp.close()

        f1 = _load(file1)
        f2 = _load(file2)
        if f1 is not None or f2 is not None:
            match_data = self.check_group(self.process_record(f1), self.process_record(f2))
        else:
            match_data = False
        _close(f1)
        _close(f2)
        return match_data

@TestMat.click_command()
def test_mat(**kwargs):
    TestMat.run(**kwargs)
