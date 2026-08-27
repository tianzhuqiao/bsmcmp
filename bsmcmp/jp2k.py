import numpy as np
import glymur

from .base import TestBaseAttr

class TestJP2K(TestBaseAttr):
    NAME = 'JP2K'
    EXT = '.jp2'

    def get_attrs(self, d):
        return {}

    def get_data(self, d):
        try:
            return np.asarray(d.astype(np.float64))
        except:
            return d

    def check_group(self, group1, group2, indent=""):

        match_attr = True
        match_data = True
        d1 = group1[:]
        d2 = group2[:]
        if d1 is None and d2 is None:
            match_data = True
        elif d1 is None or d2 is None:
            match_data = False
        else:
            match_data = self.check_data(d1, d2, indent+'    ')

        return match_data, match_attr

    def do_test(self, file1, file2):
        nc_p = glymur.Jp2k(file1)
        nc_m = glymur.Jp2k(file2)
        match_data, match_attr = self.check_group(nc_p, nc_m)
        return match_data, match_attr

    def do_stat(self, file):
        nc_p = glymur.Jp2k(file)
        self.stat_group(nc_p)

    def stat_group(self, group1, indent=""):

        # check data and its attributes
        self.start_message_delay()
        d1 = group1[:]

        if d1 is None:
            self.warning("Data is none")
            self.end_message_delay()
        else:
            self.stat_data(d1, indent+'    ')

        self.end_message_delay()


@TestJP2K.click_command()
def test_jp2k(**kwargs):
    TestJP2K.run(**kwargs)
