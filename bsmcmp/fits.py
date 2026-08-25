import numpy as np
from astropy.io import fits

from .base import TestBaseAttr

class TestFits(TestBaseAttr):
    NAME = 'Fits'
    EXT = '.fits'

    def get_attrs(self, d):
        return d.header

    def get_data(self, d):
        try:
            return np.asarray(d.astype(np.float64))
        except:
            return d

    def check_group(self, group1, group2, indent=""):

        if len(group1) != len(group2):
            self.error(f'File "{group1.filename()}" has different length from file "{group2.filename()}"')
            return False, False

        match_attr = []
        match_data = []
        for i in range(len(group1)):
            self.info(f"index {i} (group1[i].name)")
            # check attribute
            match_attr.append(self.check_attr(group1[i], group2[i], indent+'    '))

            if group1[i].data is None and group2[i].data is None:
                match_data.append(True)
                continue
            if group1[i].data is None or group2[i].data is None:
                match_data.append(False)
                continue

            if group1[i].data.dtype.names is None and group1[i].data.dtype.names is None:
                match_data.append(self.check_data(group1[i].data, group2[i].data, indent+'    '))
            elif group1[i].data.dtype.names is None or group1[i].data.dtype.names is None:
                match_data.append(False)
            else:
                match = True
                for f in group1[i].data.dtype.names:
                    if f not in group2[i].data.detyhpe.names:
                        match = False
                        break
                    match = self.check_data(group1[i].data[f], group2[i].data[f], indent+'    ', name=f)
                    if not match:
                        break
                match_data.append(match)

        return all(match_data), all(match_attr)

    def do_test(self, file1, file2):
        nc_p = fits.open(file1)
        nc_m = fits.open(file2)
        match_data, match_attr = self.check_group(nc_p, nc_m)
        nc_p.close()
        nc_m.close()
        return match_data, match_attr

    def do_stat(self, file):
        nc_p = fits.open(file)
        self.stat_group(nc_p)

    def stat_group(self, group1, indent=""):

        # check data and its attributes
        for k in range(len(group1)):
            self.start_message_delay()
            d1 = group1[k]

            self.error(f"{k}: {d1.name}", fg='green')
            if self.has_pattern(d1.name, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                self.end_message_delay()
                continue

            self.stat_attr(d1, indent+'    ')
            if d1.data is None:
                self.warning("Data is none")
                self.end_message_delay()
                continue
            if d1.data.dtype.names is None:
                self.stat_data(d1.data, indent+'    ')
            else:
                for f in d1.data.dtype.names:
                    self.stat_data(d1.data[f], indent+'    ', name=f)


            self.end_message_delay()


@TestFits.click_command()
def test_fits(**kwargs):
    TestFits.run(**kwargs)
