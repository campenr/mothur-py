"""
Copyright (c) 2017, Richard Campen
All rights reserved.

Licensed under the Modified BSD License.
For full license terms see LICENSE.txt

"""

from subprocess import PIPE, Popen, STDOUT
import collections
import os
import random


class Mothur(object):
    """
    Main class that contains configuration for mothur execution.

    """

    def __init__(self, mothur_path='mothur', current_files=None, current_dirs=None, output_files=None, verbosity=0,
                 mothur_seed=None, logfile_name=None, suppress_logfile=False, line_limit=-1):
        """

        :param mothur_path: path to the mothur executable
        :type mothur_path: str or None
        :param current_files: dictionary type object containing current files for mothur
        :type current_files: dict or None
        :param current_dirs: dictionary type object containing current directories for mothur
        :type current_dirs: dict or None
        :param output_files: dictionary type object containing lists of the latest output files from mothur
        :type output_files: collections.defaultdict(list) or None
        :param verbosity: how verbose the output should be. Can be 0, 1, or 2 where 0 is silent and 2 is most verbose.
        :type verbosity: int
        :param mothur_seed: number for mothur to seed random number generation with
        :type mothur_seed: int
        :param logfile_name: name to give the logfile
        :type logfile_name: str
        :param suppress_logfile: whether to suppress the creation of mothur logfiles
        :type suppress_logfile: bool
        :param line_limit: number of lines to output. -1 outputs all lines
        :type line_limit: int

        ..note:: the default value for mothur_path will work only if mothur is in the PATH environment variable. If
        mothur is located elsewhere, including in the current working directory, then it needs to be specified including
        the name of the executable, i.e `C:\\Path\\to\\mothur.exe` on Windows or `/path/to/mothur` on unix like systems.

        """

        if current_files is None:
            current_files = dict()
        if current_dirs is None:
            current_dirs = dict()
        if output_files is None:
            output_files = collections.defaultdict(list)

        self.mothur_path = mothur_path
        self.current_files = current_files
        self.current_dirs = current_dirs
        self.output_files = output_files
        self.verbosity = verbosity
        self.mothur_seed = mothur_seed
        self.line_limit = line_limit

        # need to define these here once so __getattr__ is not called for them
        self.suppress_logfile = suppress_logfile
        self.logfile_name = logfile_name

    def __getattribute__(self, item):
        """
         Gets attributes.

         Due to the way that @property works when __getattr__ is overloaded we can't use the decorator for getters,
         so instead we specifically catch calls to __getattribute__ for the logfile_name attributes here instead.

         """

        # we have to overload lookups for 'logfile_name'
        if item == 'logfile_name':
            return self._logfile_name

        return super().__getattribute__(item)

    def __getattr__(self, attr_name):
        """Catches unknown method calls to run them as mothur functions instead."""

        if attr_name.startswith('_'):
            # no valid mothur commands begin with underscores
            # also catches checks for potentially non-implemented dunder methods i.e. `__deepcopy__`
            raise (AttributeError('%s is not a valid mothur function.' % attr_name))

        return MothurCommand(root=self, command_name=attr_name)

    def __setattr__(self, key, value):
        """
        Sets attributes.

        Due to the way that @property works when __getattr__ is overloaded we can't use the decorator for setters,
        so instead we specifically catch calls to __setattr__ for the logfile_name attribute here instead.

        """

        if key == 'logfile_name':

            if value is not None:
                self._logfile_name = value
            else:
                # randomly generate a name
                self._logfile_name = self.generate_logfile_name()

        # otherwise fallback to default behaviour
        super().__setattr__(key, value)

    def __str__(self):
        return '<Mothur object at %s>' % int(id(self))

    @staticmethod
    def generate_logfile_name():
        """Generates logfile name for the mothur object."""

        # generate random name, iterating and checking for one that does not exist
        random.seed()
        while True:
            num = random.randint(10000, 99999)
            # construct random name and check for uniqueness
            logfile = 'mothur.py.%d.logfile' % num
            if not os.path.isfile(logfile):
                break

        return logfile


class MothurCommand(object):
    """
    Callable handler for mothur function calls generated from unknown method calls for `mothur`.

    ..note:: This class will call itself iteratively if passed an attribute until it is passed a callable
    at which point it will format the function call for mothur and execute it using mothur's command line mode.

    """

    def __init__(self, root, command_name):
        """

        :param root: the object at the root of the MothurCommand tree
        :type root: mothur_py.Mothur
        :param command_name: the name of this class instance
        :type command_name: str

        """

        self.root_object = root
        self.command_name = command_name

    def __getattr__(self, command_name):
        """

        :param command_name: the name of the attribute being requested by the calling function/class
        :type command_name: str

        ..warning: if the command_name is not a valid mothur command mothur will error.

        """

        return MothurCommand(self.root_object, '%s.%s' % (self.command_name, command_name))

    def __repr__(self):
        return 'MothurCommand(root=<%s object>, name=%r)' % (self.root_object, self.command_name)

    def __str__(self):
        return '%s.%s' % (self.root_object, self.command_name)

    def __call__(self, *args, **kwargs):
        """Catches method calls and formats and executes them as commands within mothur."""

        # --------------- initialise variables --------------- #

        # results containers
        new_current_dirs = dict()
        new_current_files = dict()
        new_output_files = collections.defaultdict(list)

        # output flags
        user_input_flag = False
        mothur_warning_flag = False
        mothur_error_flag = False
        truncate_flag = False

        # parsing flags
        parse_current_flag = False
        parse_output_flag = False

        # dict containing strings to find in lines, with matching current_dirs keys
        # mothur prints out the current directory for each category on the same line at the matched string
        current_dir_headers = {
            'Current input directory saved by mothur:': 'input',
            'Current output directory saved by mothur:': 'output',
            'Current default directory saved by mothur:': 'tempdefault'
        }
        current_dir_keys = current_dir_headers.keys()

        # --------------- format mothur input --------------- #

        mothur_args = format_mothur_params(*args, **kwargs)

        # conditionally set the seed for mothur execution
        if self.root_object.mothur_seed is not None:

            # not all mothur commands are compatible with setting the seed
            set_seed_uncompt = ['help']
            if self.command_name not in set_seed_uncompt:

                if (len(args) + len(kwargs)) > 0:
                    mothur_args = mothur_args + ',seed=%s' % self.root_object.mothur_seed
                else:
                    mothur_args = 'seed=%s' % self.root_object.mothur_seed

        # create commands
        commands = list()
        base_command = '{0}({1})'.format(self.command_name, mothur_args)
        commands.append(base_command)

        # set current files and dirs
        if self.root_object.current_files:
            current_files = ', '.join(['%s=%s' % (k, v) for k, v in self.root_object.current_files.items()])
            commands.insert(0, 'set.current(%s)' % current_files)
        if self.root_object.current_dirs:
            current_dirs = ', '.join(['%s=%s' % (k, v) for k, v in self.root_object.current_dirs.items()])
            commands.insert(0, 'set.dir(%s)' % current_dirs)
        commands.append('get.current()')

        # set logfile
        commands.insert(0, 'set.logfile(name=%s, append=T)' % self.root_object.logfile_name)

        # combine commands for mothur execution
        commands_str = '; '.join(commands)
        base_command_query = 'mothur > %s' % base_command

        # --------------- run mothur --------------- #

        p = Popen([self.root_object.mothur_path, '#%s' % commands_str], stdout=PIPE, stderr=STDOUT)

        # stdout line counter
        line_count = 0

        try:
            with p.stdout:
                for line in iter(p.stdout.readline, b''):

                    # check for valid verbosity
                    if not(0 <= self.root_object.verbosity < 3):
                        raise (ValueError('verbosity must be 0, 1, or 2.'))

                    else:

                        # strip newline characters as print statement will insert its own
                        line = line.replace(b'\r', b'')
                        line = line.rsplit(b'\n')[0]

                        # decode the line to make downstream processing easier
                        line = line.decode()

                        # ------- check for warning or error messages in mothur output ------- #

                        # mothur prints warning messages  on a line containing `[WARNING]`
                        if '[WARNING]' in line:
                            mothur_warning_flag = True

                        # mothur prints error messages on a line containing `[ERROR]`
                        if '[ERROR]' in line:
                            mothur_error_flag = True

                        # detecting invalid command as mothur does not specify this is an error but really should do
                        # see https://github.com/mothur/mothur/issues/388 for discussion of this behaviour
                        if 'Invalid command.' in line:
                            mothur_error_flag = True

                        # ------- check for output from the user specified command ------- #

                        # user input spans output from the base command until the get.current() command
                        if base_command_query in line:
                            user_input_flag = True

                            if self.root_object.verbosity == 2:
                                # add in some debug information for easier reading
                                print('\n#=============[BEGIN USER INPUT]=============#\n')

                        elif 'mothur > get.current()' in line:
                            user_input_flag = False

                            if self.root_object.verbosity == 2:
                                # add in some debug information for easier reading
                                print('\n#=============[END USER INPUT]=============#\n')

                        # ------- conditionally increment line counter and toggle truncate_flag ------- #

                        # only increment line counter for lines generated from user input
                        if user_input_flag:
                            line_count += 1

                        # check for incorrect line_limit settings, otherwise it will fail silently
                        if not -1 <= self.root_object.line_limit:
                            raise(ValueError('line_limit must be -1, 0, or any positive integer, not %s.' %
                                             self.root_object.line_limit))

                        # conditionally set truncate input flag so that we only truncate if a line limit is set
                        elif self.root_object.line_limit != -1:  # -1 signifies no line limit
                            if line_count > self.root_object.line_limit:

                                # as we only truncate output from user input the truncate_flag is the user_input_flag
                                # this allows verbosity=2 to show debug information even if line limit has been reached
                                truncate_flag = user_input_flag

                        # ------- conditionally parse current dirs and files from stdout ------- #

                        # check for current dirs
                        for key in current_dir_keys:
                            if key in line:
                                current_dir = line.split(' ')[-1].split('\n')[0]
                                new_current_dirs[current_dir_headers[key]] = current_dir

                        # conditionally reset flag for parsing current files from stdout
                        # mothur prints a blank line after the list of current files
                        if line == '':
                            parse_current_flag = False

                        # conditionally parse current files from stdout
                        if parse_current_flag:
                            current_file = line.split('=')
                            current_file_type = current_file[0]
                            current_file_name = current_file[1]
                            new_current_files[current_file_type] = current_file_name

                        # check for current files
                        # mothur prints out the current files after the line containing 'Current files saved by
                        # mothur:' so we do this check AFTER parsing current file information from the line
                        if 'Current files saved by mothur:' in line:
                            parse_current_flag = True

                        # ------- conditionally parse output files from stdout ------- #

                        # conditionally reset flag for parsing output files from stdout
                        # mothur prints a blank line after the list of output files
                        if line == '':
                            parse_output_flag = False

                        # conditionally parse current files from stdout
                        # because multiple files with the same extension can be returned we save them in a list
                        if parse_output_flag:
                            output_file_type = line.rsplit('.', 1)[-1]
                            new_output_files[output_file_type].append(line)

                        # check for output files
                        # mothur prints the output files after the line containing 'Output File Names:'
                        # so we do this check AFTER parsing output file information from the line
                        # we also check the user_input_flag to avoid saving output files from the background
                        # commands that are run to enable the 'current' keyword functionality
                        if 'Output File Names:' in line and user_input_flag:
                            parse_output_flag = True

                        # ------- conditionally print stdout from mothur to screen ------- #

                        # only print output if verbosity not zero
                        if self.root_object.verbosity > 0:

                            # only output if below the line limit if truncate_flag is set
                            if not truncate_flag:
                                # conditionally print output based on flags
                                if self.root_object.verbosity == 1:
                                    if any([user_input_flag, mothur_warning_flag, mothur_error_flag]):
                                        print(line)
                                elif self.root_object.verbosity == 2:
                                    print(line)

                            # conditionally print message to indicate line limit had been reached
                            if (self.root_object.line_limit == line_count) and user_input_flag:
                                print('\n[mothur-py WARNING]: Line limit reached. No more output will be printed.\n')


            # wait for the subprocess to finish then check for erroneous output or return code
            return_code = p.wait()

            # need to check both conditions as mothur sometimes does not return zero when it should
            if return_code != 0 or mothur_error_flag:
                raise(RuntimeError('Mothur encountered an error with return_code=%s and mothur_error_flag=%s' %
                                   (return_code, mothur_error_flag)))

        except KeyboardInterrupt:
            # tidy up running process before raising exception when keyboard interrupt detected
            # TODO: need a better way to kill the process on windows.
            p.kill()
            raise(KeyboardInterrupt('User terminated the process.'))

        finally:
            # conditionally cleanup logfile
            if self.root_object.suppress_logfile is True:
                # Mothur only renames the logfile to something predictable if it exits properly, else this will fail
                # in version 1.39.5 and earlier.
                # see https://github.com/mothur/mothur/issues/281 and https://github.com/mothur/mothur/issues/377
                try:
                    # try remove from top level directory
                    os.remove(self.root_object.logfile_name)
                except (FileNotFoundError, PermissionError) :
                    try:
                        # try removing from mothur objects output directory
                        os.remove(os.path.join(self.root_object.current_dirs['output'], self.root_object.logfile_name))
                    except (FileNotFoundError, PermissionError):
                        print('[mothur-py WARNING]: could not delete mothur logfile. '
                              'You will need to manually remove it.')

        # update root mother object with new current dirs and files
        for k, v in new_current_dirs.items():
            self.root_object.current_dirs[k] = v
        for k, v in new_current_files.items():
            self.root_object.current_files[k] = v

        # overwrite old output files with latest output files
        self.root_object.output_files = new_output_files

        return


def format_mothur_params(*args, **kwargs):
    """Formats mothur command paramters from python variables into a string formatted for mothur."""

    # list of available converter functions for making python variables mothur compatible
    converters = [
        convert_mothur_bool,
        convert_mothur_iterable
    ]

    # use the converters to alter parameter values as necessary for mothur compatibility
    formatted_args = ''
    if args:
        for arg in args:
            for converter in converters:
                arg = converter(arg)
        formatted_args = ','.join(args)

    formatted_kwargs = ''
    if kwargs:
        for k, v in kwargs.items():
            for converter in converters:
                kwargs[k] = converter(v)
        formatted_kwargs = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())

    # format command string from available command parameters
    if len(formatted_args) == 0:
        mothur_args = formatted_kwargs
    else:
        mothur_args = formatted_args
        if len(formatted_kwargs) > 0:
            mothur_args = mothur_args + ',' + formatted_kwargs

    return mothur_args


def convert_mothur_bool(item):
    """Converts python bool into a format that is compatible with mothur."""

    if item is True:
        return 'T'
    elif item is False:
        return 'F'
    else:
        return item


def convert_mothur_iterable(item):
    """Converts python iterable into a format that is compatible with mothur."""

    # convert python iterable, excluding strings, to mothur list
    if isinstance(item, collections.Sequence) and not isinstance(item, str):
        # mothur lists are hyphen separated
        return ('-').join(item)
    else:
        return item