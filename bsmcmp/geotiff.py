import numpy as np
import rasterio

from .base import TestBaseAttr

class TestGeoTiff(TestBaseAttr):
    NAME = 'GeoTIFF'
    EXT = '.tif'

    def get_attrs(self, d):
        return d.meta

    def get_data(self, d):
        return np.asarray(d[:].astype(np.float64))

    def check_group(self, group1, group2, indent=""):

        # check attribute
        match_attr = self.check_attr(group1, group2)

        # check data and its attributes
        match_data = True
        if group1.count == group2.count:
            for k in range(1, group1.count+1):
                self.start_message_delay()

                self.error(k, fg=None)
                if self.has_pattern(k, self.ignore_variables):
                    self.warning(f"{indent}    ignore")
                    self.end_message_delay()
                    continue
                d1 = group1.read(k)
                d2 = group2.read(k)
                if not self.check_data(d1, d2, indent+'    '):
                    match_data = False

                self.end_message_delay()

        return match_data, match_attr

    def do_test(self, file1, file2):
        nc_p = rasterio.open(file1)
        nc_m = rasterio.open(file2)
        match_data, match_attr = self.check_group(nc_p, nc_m)
        nc_p.close()
        nc_m.close()
        return match_data, match_attr

    def do_stat(self, file):
        nc_p = rasterio.open(file)
        self.stat_group(nc_p)

    def stat_group(self, group1, indent=""):

        # check attribute
        self.stat_attr(group1)

        # check data and its attributes
        for k in range(1, group1.count+1):
            self.start_message_delay()

            self.error(k, fg='green')
            if self.has_pattern(k, self.ignore_variables):
                self.warning(f"{indent}    ignore")
                self.end_message_delay()
                continue

            d1 = group1.read(k)
            self.stat_data(d1, indent+'    ')

            self.end_message_delay()


@TestGeoTiff.click_command()
def test_geotiff(**kwargs):
    TestGeoTiff.run(**kwargs)
