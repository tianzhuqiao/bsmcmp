import os
import traceback
import glob
import re
import functools
import click
from click.core import ParameterSource
import yaml


class TestBase:
    NAME = "base"
    def __init__(self):
        self.verbose = True
        self.ext = ".*"
        self.stop_on_mismatch = True
        self.file_count = 0
        self.mismatch_count = 0
        self._stop = False
        self.ignore_pattern = []
        self.recursive = True

    def echo(self, *args, **kwargs):
        verbose = kwargs.pop('verbose', False) or self.verbose
        if verbose:
            click.secho(*args, **kwargs)

    def error(self, *args, **kwargs):
        if 'fg' not in kwargs:
            kwargs['fg'] = 'red'
        self.echo(*args, **kwargs)

    def warning(self, *args, **kwargs):
        if 'fg' not in kwargs:
            kwargs['fg'] = 'blue'
        self.echo(*args, **kwargs)

    def success(self, *args, **kwargs):
        if 'fg' not in kwargs:
            kwargs['fg'] = 'green'
        self.echo(*args, **kwargs)

    def test(self, file1, file2):
        self.file_count += 1
        return False

    def shall_stop(self):
        return self._stop


    def has_pattern(self, value, patterns):
        for item in patterns:
            if re.search(item, value) is not None:
                return True
        return False

    def shall_ignore(self, filename):
        return self.has_pattern(filename, self.ignore_pattern)

    def show_result(self):
        self.echo(f'{self.file_count} files checked!', verbose=True)
        self.echo(f'    mismatch: {self.mismatch_count}', verbose=True)

    def test_all(self, folder1, folder2):
        self._stop = False
        if folder1 is not None and folder2 is not None:

            for filename in glob.iglob(f'{folder1}/**/*{self.ext}', recursive=self.recursive):
                if self.shall_stop():
                    break
                file1 = filename
                file2 = filename.replace(folder1, folder2)

                if self.shall_ignore(filename):
                    continue

                if not os.path.isfile(file2):
                    self.warning(f"can't find file: {file2}")
                    continue
                try:
                    match = self.test(file1, file2)
                    if not match:
                        self.echo(file1, verbose=True)
                        self.echo(file2, verbose=True)
                except:
                    self.echo(file1, verbose=True)
                    self.echo(file2, verbose=True)
                    traceback.print_exc()
                    break

            self.show_result()
            return True
        return False

    def load_config(self, **kwargs):
        if 'config' in kwargs and os.path.isfile(kwargs['config']):
            try:
                with open(kwargs['config'], 'r', encoding='utf-8') as fp:
                    cfg = yaml.safe_load(fp)
                    if self.NAME in cfg:
                        cfg = cfg[self.NAME]
                        for option in kwargs:
                            src = click.get_current_context().get_parameter_source(option)
                            if src == ParameterSource.COMMANDLINE:
                                continue
                            kwargs[option] = cfg.get(option, kwargs[option])
            except:
                self.error(f"Fail to load {kwargs['config']}", verbose=True)
                traceback.print_exc()

        self.ext = kwargs.get('ext', self.ext)
        self.stop_on_mismatch = kwargs.get('stop_on_mismatch', self.stop_on_mismatch)
        self.ignore_pattern = kwargs.get('ignore_pattern', self.ignore_pattern)
        self.recursive = kwargs.get('recursive', self.recursive)
        return kwargs


def common_options(ext, name):
    def _common_options(f):
        options = [
                click.option('--ext', default=ext, help=f'the {name} file extention'),
                click.option('--file1', type=click.Path(exists=True, dir_okay=False), help=f'1nd {name} file.'),
                click.option('--file2', type=click.Path(exists=True, dir_okay=False), help=f'2nd {name} file.'),
                click.option('--folder1', type=click.Path(exists=True, file_okay=False), help=f'1st top folder contains the {name} files.'),
                click.option('--folder2', type=click.Path(exists=True, file_okay=False), help=f'2nd top folder contains the {name} files. folder1 and folder2 shall have the same structure'),
                click.option('--stop_on_mismatch/--no-stop_on_mismatch', is_flag=True, default=True, help='Stop when see any data mismatch'),
                click.option('--ignore_pattern', '-i', multiple=True, help='filename pattern to be ignored'),
                click.option('--recursive/--no-recursive', default=True, is_flag=True, help='search the subfolders recursively'),
                click.option('--config', default='file_compare.yml', type=click.Path(exists=False, dir_okay=False), help='the configuation in yaml file'),
                ]
        return functools.reduce(lambda x, opt: opt(x), reversed(options), f)
    return _common_options
