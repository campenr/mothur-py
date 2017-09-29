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
        :param suppress_logfile: whether to supress the creation of mothur logfiles
        :type suppress_logfile: bool

        """

        self.current_files = current_files
        self.current_dirs = current_dirs
        self.verbosity = verbosity
        self.suppress_logfile = suppress_logfile

    def __getattr__(self, command_name):
        """Catches unknown method calls to run them as mothur functions instead."""

        if not command_name.startswith('_'):
            return MothurFunction(root=self, command_name=command_name)

        raise (AttributeError('%s is not a valid mothur function.' % command_name))

    def __repr__(self):
        return 'Mothur(current_files=%r, current_dirs=%r, parse_current_file=%r, parse_log_file=%r, verbosity=%r)' % \
               (self.current_files, self.current_dirs, self.parse_current_file, self.parse_log_file, self.verbosity)

    def __str__(self):
        return 'rhea.Mothur'


class MothurFunction:
    """
    Callable handler for mothur function calls generated from unknown method calls for `mothur`.

    ..note:: This class will call itself iteratively if passed an attribute until it is passed a callable
    at which point it with format the function call for mothur and execute it using mothur's batch mode.

    """

    def __init__(self, root, command_name):
        """

        :param root: the object at the root of the mothur and mothurFunction tree
        :type root: rhea.core.Mothur
        :param command_name: the name of this class instance
        :type command_name: str

        """

        self._root = root
        self._command_name = command_name

    def __getattr__(self, command_name):
        """

        :param command_name: the name of the attribute being requested by the calling function/class
        :type command_name: str

        :return: a new MothurFunction instance with self.parent set to this MothurFunction instance.
        :returns: rhea.core.MothurFunction

        """

        if not command_name.startswith('_'):
            return MothurFunction(self._root, '%s.%s' % (self._command_name, command_name))

        raise (AttributeError('{} is not a valid mothur function.'.format(command_name)))

    def __repr__(self):
        return 'MothurFunction(root=<%s object>, name=%r)' % (self._root, self._command_name)

    def __str__(self):
        return '%s.%s' % (self._root, self._command_name)

    def __call__(self, *args, **kwargs):
        """
        Catches method calls and formats and executes them as commands within mothur.

        """

        # extract name of mothur command
        mothur_command = self._command_name

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
        base_command = '{0}({1})'.format(mothur_command, mothur_args)
        commands.append(base_command)
        if self._root.current_files:
            current_files = ', '.join(['%s=%s' % (k, v) for k, v in self._root.current_files.items()])
            commands.insert(0, 'set.current(%s)' % current_files)
        if self._root.current_dirs:
            current_dirs = ', '.join(['%s=%s' % (k, v) for k, v in self._root.current_dirs.items()])
            commands.insert(0, 'set.dir(%s)' % current_dirs)
        commands.append('get.current()')

        if self._root.suppress_logfile:
            # force name of mothur logfile
            logfile = 'mothur.rhea.logfile'
        else:
            random.seed()
            while True:
                # iterate random names, checking it does not exists already
                rn = random.randint(10000, 99999)
                logfile_path = 'mothur.rhea.%d.logfile' % rn

                out_dir = self._root.current_dirs.get('output', False)
                if out_dir:
                    logfile_path = os.path.join(out_dir, logfile_path)
                if not os.path.isfile(logfile_path):
                    logfile = logfile_path
                    break
        commands.insert(0, 'set.logfile(name=%s)' % logfile)

        # format commands for mothur execution
        commands_str = '; '.join(commands)

        # output flags
        user_input_flag = False
        mothur_error_flag = False

        # setup byte encoded strings for conditional printing
        base_command_bytes = base_command
        get_current_bytes = 'mothur > get.current()'
        mothur_warning_bytes = '<<<'
        mothur_error_bytes = '***'

        # parsing flags
        parse_current_flag = False

        # setup byte encoded strings for conditional output parsing
        current_dir_bytes = {
            'Current input directory saved by mothur:': 'input',
            'Current output directory saved by mothur:': 'output',
            'Current default directory saved by mothur:': 'tempdefault'
        }
        current_dir_bytes_keys = current_dir_bytes.keys()
        current_files_bytes = 'Current files saved by mothur:'

        # run mothur command in command line mode
        p = Popen(['mothur', '#%s' % commands_str], stdout=PIPE, stderr=STDOUT)

        try:
            with p.stdout:
                for line in iter(p.stdout.readline, b''):

                    # check for valid verbosity setting
                    if 0 <= self._root.verbosity < 3:

                        # strip newline characters as print statement will insert its own
                        line = line.replace(b'\r', b'')
                        line = line.rsplit(b'\n')[0]

                        # decode the line to make downstream processing easier
                        line = line.decode()

                        # only print output if verbosity not zero
                        if self._root.verbosity > 0:

                            # conditionally set user_input_flag
                            if base_command_bytes in line:
                                user_input_flag = True
                            elif get_current_bytes in line:
                                user_input_flag = False

                            # conditionally set mothur_error_flag
                            if mothur_warning_bytes in line or mothur_error_bytes in line:
                                mothur_error_flag = True

                        if self._root.verbosity == 1:
                            if any([user_input_flag, mothur_error_flag]):
                                print(line)
                                # print(line.decode())
                        elif self._root.verbosity == 2:
                            print(line)
                            # print(line.decode())

                        # check for current dirs
                        for key in current_dir_bytes_keys:
                            if key in line:
                                current_dir = line.split(' ')[-1].split('\n')[0]
                                self._root.current_dirs[current_dir_bytes[key]] = current_dir

                        # conditionally reset flag for parsing current files from stdout
                        if line == '':
                            parse_current_flag = False

                        # save current files while parse flag is true
                        if parse_current_flag:
                            current_file = line.split('=')
                            current_file_type = current_file[0]
                            current_file_name = current_file[1]
                            self._root.current_files[current_file_type] = current_file_name

                        # check for current files
                        if current_files_bytes in line:
                            parse_current_flag = True

                    else:
                        raise(ValueError('verbosity must be 0, 1, or 2.'))

            return_code = p.wait()  # wait for the subprocess to finish
            if return_code != 0:
                raise(MothurError('Mothur encounted an error.'))

            return self._root

        except KeyboardInterrupt:
            # tidy up running process before raising exception when keyboard interrupt detected
            p.terminate()
            raise(KeyboardInterrupt('User terminated process.'))

        except MothurError as e:
            raise e

        finally:
            # conditionally cleanup logfile
            if self._root.suppress_logfile is True:
                # need to append output directory to logfile path if it has been set else
                out_dir = self._root.current_dirs.get('output', False)
                if out_dir:
                    logfile = os.path.join(out_dir, logfile)

                # TODO: Mothur only renames the logfile to something predictable if exits properly, else this will fail
                try:
                    os.remove(logfile)
                except FileNotFoundError:
                    print('[WARNING]: could not delete mothur logfile')


class MothurError(Exception):

    def __init__(self, *args, **kwargs):
        pass
