import click

from .version import __version__
from .ascii import test_ascii

@click.group()
@click.version_option(__version__)
def cli():
    pass

cli.add_command(test_ascii)
try:
    from .netcdf import test_netcdf
    cli.add_command(test_netcdf)
except:
    pass

try:
    from .h5 import test_h5
    cli.add_command(test_h5)
except:
    pass

try:
    from .mat import test_mat
    cli.add_command(test_mat)
except:
    pass

from .csv import test_csv
try:
    from .csv import test_csv
    cli.add_command(test_csv)
except:
    pass

if __name__ == '__main__':
    cli()
