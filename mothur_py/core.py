"""
Copyright (c) 2017, Richard Campen
All rights reserved.

Licensed under the Modified BSD License.
For full license terms see LICENSE.txt

"""

# mothur-py v0.2.1

from subprocess import PIPE, Popen, STDOUT
import random
import os


class Mothur:
    """
    Main class that contains configuration for mothur execution.

    """

    def __init__(self, current_files=None, current_dirs=None, verbosity=0, suppress_logfile=False):
        """

        :param current_files: dictionary type object containing current files for mothur
        :type current_files: dict
        :param verbosity: how verbose the output should be. Can be 0, 1, or 2 where 0 is silent and 2 is most verbose.
        :type verbosity: int
        :param suppress_logfile: whether to suppress the creation of mothur logfiles
        :type suppress_logfile: bool

        """

        if current_files is None:
            current_files = dict()
        if current_dirs is None:
            current_dirs = dict()

        self.current_files = current_files
        self.current_dirs = current_dirs
        self.verbosity = verbosity
        self.suppress_logfile = suppress_logfile

    def __getattr__(self, command_name):
        """Catches unknown method calls to run them as mothur functions instead."""

        return MothurCommand(root=self, command_name=command_name)


class MothurCommand:
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

        # output flags
        user_input_flag = False
        mothur_warning_flag = False
        mothur_error_flag = False

        # parsing flags
        parse_current_flag = False

        # dict containing strings to find in lines, with matching current_dirs keys
        # mothur prints out the current directory for each category on the same line at the matched string
        current_dir_headers = {
            'Current input directory saved by mothur:': 'input',
            'Current output directory saved by mothur:': 'output',
            'Current default directory saved by mothur:': 'tempdefault'
        }
        current_dir_keys = current_dir_headers.keys()

        # --------------- format mothur input --------------- #

        # get and format arguments for mothur command call
        formatted_args = ''
        formatted_kwargs = ''

        # format mothur command arguments
        if args:
            formatted_args = ','.join(args)
        if kwargs:
            formatted_kwargs = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())

        if len(formatted_args) == 0:
            mothur_args = formatted_kwargs
        else:
            mothur_args = formatted_args
            if len(formatted_kwargs) > 0:
                mothur_args = mothur_args + ',' + formatted_kwargs

        # create commands
        commands = list()
        base_command = '{0}({1})'.format(self.command_name, mothur_args)
        commands.append(base_command)
        if self.root_object.current_files:
            current_files = ', '.join(['%s=%s' % (k, v) for k, v in self.root_object.current_files.items()])
            commands.insert(0, 'set.current(%s)' % current_files)
        if self.root_object.current_dirs:
            current_dirs = ', '.join(['%s=%s' % (k, v) for k, v in self.root_object.current_dirs.items()])
            commands.insert(0, 'set.dir(%s)' % current_dirs)
        commands.append('get.current()')

        # create logfile name
        if self.root_object.suppress_logfile:
            # force name of mothur logfile
            logfile = 'mothur.py.logfile'
        else:
            random.seed()
            while True:
                # iterate random names, checking it does not exists already
                rn = random.randint(10000, 99999)
                logfile_path = 'mothur.py.%d.logfile' % rn

                out_dir = self.root_object.current_dirs.get('output', '')
                if out_dir:
                    logfile_path = os.path.join(out_dir, logfile_path)
                if not os.path.isfile(logfile_path):
                    logfile = logfile_path
                    break
        commands.insert(0, 'set.logfile(name=%s)' % logfile)

        # combine commands for mothur execution
        commands_str = '; '.join(commands)
        base_command_query = 'mothur > %s' % base_command

        # --------------- run mothur --------------- #

        # run mothur command in command line mode
        # TODO: add support for variable mothur executable locations
        p = Popen(['mothur', '#%s' % commands_str], stdout=PIPE, stderr=STDOUT)

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

                        # mothur prints warning messages starting with a string containing '<<<'
                        if '<^>' in line:
                            mothur_warning_flag = True

                        # mothur prints error messages starting with a string containing '***'
                        if '***' in line:
                            mothur_error_flag = True

                        # detecting invalid command as mothur does not specify this is an error but really should do
                        # see https://github.com/mothur/mothur/issues/388 for discussion of this behaviour
                        if 'Invalid command.' in line:
                            mothur_error_flag = True

                        # ------- conditionally parse current dirs and files from output ------- #

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

                        # ------- conditionally print output from mothur to screen ------- #

                        # only print output if verbosity not zero
                        if self.root_object.verbosity > 0:

                            # conditionally set flags
                            # user input spans output from the base command until the get.current() command
                            if base_command_query in line:
                                user_input_flag = True
                            elif 'mothur > get.current()' in line:
                                user_input_flag = False

                            # conditionally print output based on flags
                            if self.root_object.verbosity == 1:
                                if any([user_input_flag, mothur_warning_flag, mothur_error_flag]):
                                    print(line)
                            elif self.root_object.verbosity == 2:
                                print(line)

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
            # update root mother object with new current dirs and files
            for k, v in new_current_dirs.items():
                self.root_object.current_dirs[k] = v
            for k, v in new_current_files.items():
                self.root_object.current_dirs[k] = v

            # conditionally cleanup logfile
            if self.root_object.suppress_logfile is True:
                # need to append output directory to logfile path if it has been set else we won't be able to find it
                out_dir = self.root_object.current_dirs.get('output', '')
                if out_dir:
                    logfile = os.path.join(out_dir, logfile)

                # Mothur only renames the logfile to something predictable if exits properly, else this will fail
                # see https://github.com/mothur/mothur/issues/281 and https://github.com/mothur/mothur/issues/377
                try:
                    os.remove(logfile)
                except FileNotFoundError:
                    print('[WARNING]: could not delete mothur logfile. You will need to manually remove it.')

        return
