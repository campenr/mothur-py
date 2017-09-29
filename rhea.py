from subprocess import PIPE, Popen, STDOUT
import random
import os


class Mothur:
    """
    Main class that contains configuration for mothur execution and catches mothur function calls.

    """

    def __init__(self, current_files=dict(), current_dirs=dict(), parse_current_file=False,
                 parse_log_file=False, verbosity=0, suppress_logfile=False):
        """

        :param current_files: dictionary type object containing current files for mothur
        :type current_files: dict
        :param parse_current_file: whether to parse the current files from the current.files file output by mothur
        :type parse_current_file: bool
        :param parse_log_file: whether to parse the current files from the log file output by mothur
        :type parse_log_file: bool
        :param verbosity: how verbose the output should be. Can be 0, 1, or 2 where 0 is silent and 2 is most verbose.
        :type verbosity: int
        :param suppress_logfile: whether to supress the creation of mothur logfiles
        :type suppress_logfile: bool

        """

        self.current_files = current_files
        self.current_dirs = current_dirs

        self.parse_current_file = parse_current_file
        self.parse_log_file = parse_log_file
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
        return 'MothurFunction(root=%r, name=%r)' % (self._root, self._command_name)

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
        base_command_bytes = base_command.encode()
        get_current_bytes = 'mothur > get.current()'.encode()
        mothur_warning_bytes = '<<<'.encode()
        mothur_error_bytes = '***'.encode()

        # run mothur command in command line mode
        p = Popen(['mothur', '#%s' % commands_str], stdout=PIPE, stderr=STDOUT)

        try:
            with p.stdout:
                for line in iter(p.stdout.readline, b''):

                    # check for valid verbosity setting
                    if 0 <= self._root.verbosity < 3:

                        # only print output if verbosity not zero
                        if self._root.verbosity > 0:
                            # strip newline characters as print statement will insert its own
                            line = line.replace(b'\r', b'')
                            line = line.rsplit(b'\n')[0]

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
                                print(line.decode())
                        elif self._root.verbosity == 2:
                            print(line.decode())

                    else:
                        raise(ValueError('verbosity must be 0, 1, or 2.'))

            return_code = p.wait()  # wait for the subprocess to finish
            if return_code != 0:
                raise(MothurError('Mothur encounted an error.'))

            # TODO parse output files from stdout instead
            if self._root.parse_log_file:
                # update root objects from mothur output, then return updated object
                current_files, dirs = self._parse_output(logfile)
                self._root.current_files = current_files
                self._root.current_dirs = dirs

        except KeyboardInterrupt:
            # tidy up running process before raising exception when keyboard interrupt detected
            p.terminate()
            raise(KeyboardInterrupt('User terminated process.'))

        finally:
            # conditionally cleanup logfile
            if self._root.suppress_logfile is True:
                # need to append output directory to logfile path if it has been set else
                out_dir = self._root.current_dirs.get('output', False)
                if out_dir:
                    logfile = os.path.join(out_dir, logfile)

                # will raise an error if a KeyboardInterrupt is placed. Need to deal with this better.
                os.remove(logfile)

        return self._root

    @staticmethod
    def _parse_output(output):
        """
        Parses mothur logfile to extract current files.

        :param output: file name of logfile containing mothur output
        :type output: str

        """

        HEADERS = {
            'Current input directory saved by mothur:': 'input',
            'Current output directory saved by mothur:': 'output',
            'Current default directory saved by mothur:': 'tempdefault'
        }

        current_files = {}
        dirs = {}
        with open(output, 'r') as log:
            lines = (line for line in log.readlines())
            for line in lines:
                if 'Current files saved by mothur:' in line:
                    while True:
                        try:
                            output_file = (next(line for line in lines)).split()
                            if output_file:
                                file_type = output_file[0].split('=')[0]
                                file_name = output_file[0].split('=')[1]
                                current_files[file_type] = file_name
                            else:
                                break
                        except StopIteration:
                            break
                for k, v in HEADERS.items():
                    if k in line:
                        mothur_dir = line.split(' ')[-1].split('\n')[0]
                        dirs[v] = mothur_dir

        return current_files, dirs


class MothurError(Exception):

    def __init__(self, *args, **kwargs):
        pass
