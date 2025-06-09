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

if __name__ == '__main__':
    cli()
