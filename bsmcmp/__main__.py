import click
from auto_click_auto import enable_click_shell_completion
from auto_click_auto.utils import detect_shell

from .version import __version__, PROJECT_NAME
from .ascii import test_ascii

@click.group()
@click.version_option(__version__)
def cli():
    pass

@click.command()
@click.option('--shell_completion', is_flag=True, help='Enable command autocompletion')
def config(shell_completion):
    if shell_completion:
        enable_click_shell_completion(program_name=PROJECT_NAME, verbose=True)
try:
    # if not supported, detect_shell will throw an exception
    detect_shell()
    cli.add_command(config)
except:
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
    from .grib2 import test_grib2
    cli.add_command(test_grib2)
except:
    pass

try:
    from .mat import test_mat
    cli.add_command(test_mat)
except:
    pass

try:
    from .csv import test_csv
    cli.add_command(test_csv)
except:
    pass

try:
    from .geotiff import test_geotiff
    cli.add_command(test_geotiff)
except:
    pass


if __name__ == '__main__':
    cli()
