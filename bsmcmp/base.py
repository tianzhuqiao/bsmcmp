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
    LOG_NONE = 0
    LOG_ERROR = 1
    LOG_WARN = 2
    LOG_INFO = 3
    LOG_DEBUG = 4
    LOG_MAX = 5
    LOG_AUTO = 6

    def __init__(self):
        self.verbose = self.LOG_INFO
        self.ext = self.EXT
        self.stop_on_mismatch = True
        self.file_count = 0
        self.mismatch_count = 0
        self._stop = False
        self.ignore_pattern = []
        self.recursive = True
        self.tqdm_mode = False
        self._msgs = []
        self.message_delay = 0
        self.match = False

    def _verbose(self, kwargs):
        return kwargs.pop('verbose', 0) or self.verbose

    def start_message_delay(self):
        self.message_delay += 1

    def end_message_delay(self, min_msg_to_flush=2):
        self.message_delay -= 1
        if self.message_delay == 0:
            if len(self._msgs) >= min_msg_to_flush:
                self.flush()
            self._msgs = []

    def flush(self):
        for args, kwargs in self._msgs:
            self._echo(*args, **kwargs)
        self._msgs = []

    def echo(self, *args, **kwargs):
        if self.message_delay:
            self._msgs.append([args, kwargs])
            return
        self._echo(*args, **kwargs)

    def _echo(self, *args, **kwargs):
        if not self.tqdm_mode:
            click.secho(*args, **kwargs)
        else:
            end = '\n'
            if not kwargs.get('nl', True):
                end = ''
            kwargs.pop('nl', None)
            tqdm.tqdm.write(click.style(*args, **kwargs), end=end)

    def info(self, *args, **kwargs):
        if self._verbose(kwargs) < self.LOG_INFO:
            return
        self.echo(*args, **kwargs)

    def error(self, *args, **kwargs):
        if self._verbose(kwargs) < self.LOG_ERROR:
            return
        if 'fg' not in kwargs:
            kwargs['fg'] = 'red'
        self.echo(*args, **kwargs)

    def warning(self, *args, **kwargs):
        if self._verbose(kwargs) < self.LOG_WARN:
            return
        if 'fg' not in kwargs:
            kwargs['fg'] = 'blue'
        self.echo(*args, **kwargs)

    def success(self, *args, **kwargs):
        if 'fg' not in kwargs:
            kwargs['fg'] = 'green'
        self.info(*args, **kwargs)

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
        self.info(f'{self.file_count} files checked!', verbose=self.LOG_MAX)
        self.info('    mismatch: ', nl=False, verbose=self.LOG_MAX)
        if self.mismatch_count > 0:
            self.error(f'{self.mismatch_count}', verbose=self.LOG_MAX)
        else:
            self.success(f'{self.mismatch_count}', verbose=self.LOG_MAX)

    def show_pass_fail(self, name, match, verbose):
        if match:
            self.success(f'    {name}: ', fg=None, nl=False, verbose=verbose)
            self.success('pass', verbose=verbose)
        else:
            self.error(f'    {name}: ', fg=None, nl=False, verbose=verbose)
            self.error('fail', verbose=verbose)

    def show_overall(self):
        verbose = self.verbose if self.tqdm_mode else self.LOG_MAX
        self.info("--------", verbose=verbose)
        self.info("overall:", verbose=verbose)
        self.show_pass_fail('data', self.match, verbose)

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
                self.error(f"\n#{self.file_count+1}", fg=None)
                self.error(file1, fg=None)
                self.error(file2, fg=None)
                if not os.path.isfile(file2):
                    self.warning(f"can't find file: {file2}")
                    continue
                try:
                    match = self.test(file1, file2)
                    if not match and self.verbose == self.LOG_NONE:
                        self.info(f"\n#{self.mismatch_count} mismatch", verbose=self.LOG_MAX)
                        self.info(file1, verbose=self.LOG_MAX)
                        self.info(file2, verbose=self.LOG_MAX)
                except:
                    if self.verbose == self.LOG_NONE:
                        self.info(file1, verbose=self.LOG_MAX)
                        self.info(file2, verbose=self.LOG_MAX)
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

        self.verbose = kwargs.get('verbose', self.verbose)
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
            if test.verbose == test.LOG_AUTO:
                test.verbose = test.LOG_INFO
            test.test(kwargs['file1'], kwargs['file2'])
            test.show_result()
            return
        if kwargs['folder1'] is not None and kwargs['folder2'] is not None:
            if test.verbose == test.LOG_AUTO:
                test.verbose = test.LOG_NONE
            test.test_all(kwargs['folder1'], kwargs['folder2'])

    @classmethod
    def get_options(cls):
        return [
                click.option('-v', '--verbose', default=cls.LOG_AUTO, count=True),
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
            self.error(f"{indent}data: ", fg=None, nl=False)
            self.error("fail")
            err = np.abs(d1 - d2)
            w = np.argwhere(err == np.max(err))
            n_zero_err = np.sum((err.flatten() == 0))
            n_all = len(err.flatten())

            self.error(f"{indent}    max error: {np.nanmax(err):.6g} at", fg=None)
            self.error(f"{indent}              " + str(w).replace('\n', f'\n{indent}              '), fg=None)
            self.error(f"{indent}        d1[0]: {d1[tuple(w[0])]}", fg=None)
            self.error(f"{indent}        d2[0]: {d2[tuple(w[0])]}", fg=None)
            self.error(f"{indent}    avg error: {np.nanmean(err):.6g}", fg=None)
            self.error(f"{indent}    std error: {np.nanstd(err):.6g}", fg=None)
            self.error(f"{indent}      0 error: {n_zero_err/n_all*100:.4f}% ({n_zero_err}/{n_all})", fg=None)

        else:
            self.success(f"{indent}data: ", fg=None, nl=False)
            self.success("pass")

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

        self.match = match_data
        self.show_overall()

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
        self.match_attr = False

    def get_attrs(self, d):
        raise NotImplementedError

    def check_attr(self, d1, d2, indent=''):
        # a1, a2 are attribute dict
        a1 = self.get_attrs(d1)
        a2 = self.get_attrs(d2)

        match = True
        if sorted(a1.keys()) != sorted(a2.keys()):
            self.error(f"{indent}different attributes")
            self.error(f"{indent}    {sorted(a1.keys())}", fg=None)
            self.error(f"{indent}    {sorted(a2.keys())}", fg=None)

        for att in a1:
            if att not in a2:
                continue
            if self.has_pattern(att, self.ignore_attributes):
                self.warning(f"{indent}{att}: ignore")
                continue

            if a1[att] != a2[att]:
                match = False
                self.error(f"{indent}{att}: ", fg=None, nl=False)
                self.error("fail")
                self.error(f"{indent}    {repr(a1[att])}", fg=None)
                self.error(f"{indent}    {repr(a2[att])}", fg=None)
            else:
                self.success(f"{indent}{att}: ", fg=None, nl=False)
                self.success("pass")
        return match

    def test(self, file1, file2):
        TestBase.test(self, file1, file2)

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

        self.match = match_data
        self.match_attr = match_attr
        self.show_overall()

        return match_data

    def show_overall(self):
        super().show_overall()
        verbose = self.verbose if self.tqdm_mode else self.LOG_MAX
        self.show_pass_fail('attribute', self.match_attr, verbose)

    def load_config(self, **kwargs):
        kwargs = super().load_config(**kwargs)
        self.stop_on_attr_mismatch = kwargs.get('stop_on_attr_mismatch', self.stop_on_attr_mismatch)
        self.ignore_attributes = kwargs.get('ignore_attr', [])
        return kwargs

    def show_result(self):
        super().show_result()
        self.info('    attribute mismatch: ', nl=False, verbose=self.LOG_MAX)
        if self.mismatch_attr > 0:
            self.error(f'{self.mismatch_attr}', verbose=self.LOG_MAX)
        else:
            self.success(f'{self.mismatch_attr}', verbose=self.LOG_MAX)

    @classmethod
    def run(cls, **kwargs):
        test = cls()
        kwargs = test.load_config(**kwargs)
        if kwargs['file1'] is not None and kwargs['file2'] is not None:
            test.stop_on_mismatch = False
            test.stop_on_attr_mismatch = False
            if test.verbose == test.LOG_AUTO:
                test.verbose = test.LOG_INFO
            test.test(kwargs['file1'], kwargs['file2'])
            test.show_result()
        elif kwargs['folder1'] is not None and kwargs['folder2'] is not None:
            if test.verbose == test.LOG_AUTO:
                test.verbose = cls.LOG_NONE
            test.test_all(kwargs['folder1'], kwargs['folder2'])

    @classmethod
    def get_options(cls):
        return super().get_options() + [
                click.option('--stop_on_attr_mismatch', is_flag=True, default=False, help='Stop when see any attribute mismatch'),
                click.option('--ignore_attr', multiple=True, help='attributes to be ignored')
                ]
