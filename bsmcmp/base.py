import os
import traceback
import glob
import re
import functools
import numpy as np
import click
from click.core import ParameterSource
import yaml
import tqdm

class TestBase:
    NAME = "base"
    EXT = ".*"
    def __init__(self):
        self.verbose = True
        self.ext = self.EXT
        self.stop_on_mismatch = True
        self.file_count = 0
        self.mismatch_count = 0
        self._stop = False
        self.ignore_pattern = []
        self.recursive = True
        self.tqdm_mode = False

    def echo(self, *args, **kwargs):
        verbose = kwargs.pop('verbose', False) or self.verbose
        if verbose:
            if not self.tqdm_mode:
                click.secho(*args, **kwargs)
            else:
                tqdm.tqdm.write(*args)

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
            self.tqdm_mode = True
            for filename in tqdm.tqdm(glob.iglob(f'{folder1}/**/*{self.ext}', recursive=self.recursive)):
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

            self.tqdm_mode = False
            self.show_result()
            return True
        return False

    def load_config(self, **kwargs):
        if 'config' in kwargs and os.path.isfile(kwargs['config']):
            try:
                with open(kwargs['config'], 'r', encoding='utf-8') as fp:
                    cfg = yaml.safe_load(fp)
                    if self.NAME.lower() in cfg:
                        cfg = cfg[self.NAME.lower()]
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

    @classmethod
    def run(cls, **kwargs):
        test = cls()
        kwargs = test.load_config(**kwargs)
        if kwargs['file1'] is not None and kwargs['file2'] is not None:
            test.stop_on_mismatch = False
            test.verbose = True
            test.test(kwargs['file1'], kwargs['file2'])
            test.show_result()
            return
        if kwargs['folder1'] is not None and kwargs['folder2'] is not None:
            test.verbose = False
            test.test_all(kwargs['folder1'], kwargs['folder2'])

    @classmethod
    def get_options(cls):
        return [
                click.option('--ext', default=cls.EXT, help=f'the {cls.NAME} file extention'),
                click.option('--file1', type=click.Path(exists=True, dir_okay=False), help=f'1nd {cls.NAME} file.'),
                click.option('--file2', type=click.Path(exists=True, dir_okay=False), help=f'2nd {cls.NAME} file.'),
                click.option('--folder1', type=click.Path(exists=True, file_okay=False), help=f'1st top folder contains {cls.NAME} files.'),
                click.option('--folder2', type=click.Path(exists=True, file_okay=False), help=f'2nd top folder contains {cls.NAME} files. folder1 and folder2 shall have the same structure'),
                click.option('--stop_on_mismatch/--no-stop_on_mismatch', is_flag=True, default=True, help='Stop when see any data mismatch'),
                click.option('--ignore_pattern', '-i', multiple=True, help='filename pattern to be ignored'),
                click.option('--recursive/--no-recursive', default=True, is_flag=True, help='search the subfolders recursively'),
                click.option('--config', default='file_compare.yml', type=click.Path(exists=False, dir_okay=False), help='the configuation in yaml file'),
                ]

    @classmethod
    def click_command(cls):
        def _common_options(f):
            options = [click.command(cls.NAME.lower(), context_settings={'show_default': True})]
            options += cls.get_options()

            return functools.reduce(lambda x, opt: opt(x), reversed(options), f)
        return _common_options

class TestBaseGroup(TestBase):
    NAME = 'TestBaseGroup'
    def __init__(self):
        super().__init__()
        self.ignore_variables = []

    def get_data(self, d):
        raise NotImplementedError

    def check_data(self, d1, d2, indent=''):
        d1 = self.get_data(d1)
        d2 = self.get_data(d2)
        match = True
        if d1.shape == d2.shape:
            if not d1.shape:
                # empty variable
                match = True
            else:
                # equal_nan is not supported for non-numeric data type
                match = np.array_equal(d1, d2, equal_nan= np.issubdtype(d1.dtype, np.number))
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

        raise NotImplementedError

    def do_test(self, file1, file2):

        raise NotImplementedError

    def test(self, file1, file2):
        super().test(file1, file2)

        match_data = self.do_test(file1, file2)
        if not match_data:
            self.mismatch_count += 1

        if self.stop_on_mismatch and not match_data:
            self._stop = True
            self.error("data mismatch")

        self.echo("--------")
        self.echo("overall:")
        if match_data:
            self.success('    data: pass')
        else:
            self.error('    data: fail')
        return match_data


    def load_config(self, **kwargs):
        kwargs = super().load_config(**kwargs)
        self.ignore_variables = kwargs.get('ignore_var', [])
        return kwargs

    @classmethod
    def get_options(cls):
        return super().get_options() + [
                click.option('--ignore_var', multiple=True, help='variables to be ignored'),
                ]

class TestBaseAttr(TestBaseGroup):
    NAME = 'TestBaseAttr'
    def __init__(self):
        super().__init__()
        self.mismatch_attr = 0
        self.stop_on_attr_mismatch = False
        self.ignore_attributes = []

    def get_attrs(self, d):
        raise NotImplementedError

    def check_attr(self, d1, d2, indent=''):
        # a1, a2 are attribute dict
        a1 = self.get_attrs(d1)
        a2 = self.get_attrs(d2)

        match = True
        if sorted(a1.keys()) != sorted(a2.keys()):
            self.error(f"{indent}different attributes")
            self.echo(f"{indent}    {sorted(a1.keys())}")
            self.echo(f"{indent}    {sorted(a2.keys())}")

        for att in a1:
            if att not in a2:
                continue
            if self.has_pattern(att, self.ignore_attributes):
                self.warning(f"{indent}{att}: ignore")
                continue

            if a1[att] != a2[att]:
                match = False
                self.error(f"{indent}{att}: fail")
                self.echo(f"{indent}    {a1[att]}")
                self.echo(f"{indent}    {a2[att]}")
            else:
                self.success(f"{indent}{att}: pass")
        return match

    def test(self, file1, file2):
        super().test(file1, file2)

        match_data, match_attr = self.do_test(file1, file2)
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


    def load_config(self, **kwargs):
        kwargs = super().load_config(**kwargs)
        self.stop_on_attr_mismatch = kwargs.get('stop_on_attr_mismatch', self.stop_on_attr_mismatch)
        self.ignore_attributes = kwargs.get('ignore_att', [])
        return kwargs

    def test_all(self, folder1, folder2):
        if super().test_all(folder1, folder2):
            self.echo(f'    attribute mismatch: {self.mismatch_attr}', verbose=True)

    @classmethod
    def run(cls, **kwargs):
        test = cls()
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

    @classmethod
    def get_options(cls):
        return super().get_options() + [
                click.option('--stop_on_attr_mismatch', is_flag=True, default=False, help='Stop when see any attribute mismatch'),
                click.option('--ignore_att', multiple=True, help='attributes to be ignored')
                ]
