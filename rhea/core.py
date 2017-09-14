from subprocess import call
import random

class Mothur:
    """
    Main class that contains configuration for mothur execution and catches mothur function calls.
    
    """

    def __init__(self, name='mothur', current_files=None, current_dirs=None, parse_current_file=False,
                 parse_log_file=False, display_output=False):
        """
        
        :param name: name of the mothur object
        :type name: str
        :param current_files: dictionary type object containing current files for mothur
        :type current_files: dict
        :param parse_current_file: whether to parse the current files from the current.files file output by mothur
        :type parse_current_file: bool
        :param parse_log_file: whether to parse the current files from the log file output by mothur
        :type parse_log_file: bool
        :param display_logfile: whether to print the contents of the mothur logfile
        :type display_logfile: bool   
        
        """
        self._name = name

        self.current_files = current_files
        self.current_dirs = current_dirs

        self.parse_current_file = parse_current_file
        self.parse_log_file = parse_log_file
        self.display_output = display_output

    def __getattr__(self, name):
        """Catches unknown method calls to run them as mothur functions instead."""

        if not name.startswith('_'):
            return MothurFunction(self, self, name)

        raise (AttributeError('{} is not a valid mothur function.'.format(name)))


class MothurFunction:
    """
    Callable handler for mothur function calls generated from unknown method calls for `mothur`.
    
    ..note:: This class will call itself iteratively if passed an attribute until it is passed a callable
    at which point it with format the function call for mothur and execute it using mothur's batch mode.

    """
    def __init__(self, root, parent, name):
        """
        Instantiates a MothurFunction instance.
        
        :param root: the object at the root of the mothur and mothurFunction tree
        :type root: rhea.core.Mothur
        :param parent: the object that created this class instance
        :type parent: rhea.core.Mothur or rhea.core.MothurFunction
        :param name: the name of this class instance       
        :type name: str
        
        """

        self._root = root
        self._parent = parent
        self._name = parent._name + '.' + name

    def __getattr__(self, name):
        """
        Creates a child MothurFunction object.
        
        :param name: the name of the attribute being requested by the calling function/class
        :type name: str
        
        :return: a new MothurFunction instance with self.parent set to this MothurFunction instance.
        :returns: rhea.core.MothurFunction
        
        """

        if not name.startswith('_'):
            return MothurFunction(self._root, self, name)

        raise(AttributeError('{} is not a valid mothur function.'.format(name)))

    def __call__(self, *args, **kwargs):
        """
        Catches method calls and formats and executes them as commands within mothur.
                
        """

        # extract name of mothur command
        mothur_command = self._name.split('.', 1)[1]

        # get and format arguments for mothur command call
        formatted_args = ''
        formatted_kwargs = ''

        # format mothur command arguments
        if args:
            formatted_args = ','.join(args)
        if kwargs:
            formatted_kwargs = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())

        if len(formatted_args) == 0:
            mothur_args  = formatted_kwargs
        else:
            mothur_args = formatted_args
            if len(formatted_kwargs) > 0:
                mothur_args = mothur_args + ',' + formatted_kwargs

        # create commands
        commands = list()
        base_command = '{0}({1})'.format(mothur_command, mothur_args)
        commands.append(base_command)
        if self._root.current_files is not None:
            current_files = ', '.join(['%s=%s' % (k, v) for k, v in self._root.current_files.items()])
            commands.insert(0, 'set.current(%s)' % current_files)
        if self._root.current_dirs is not None:
            current_dirs = ', '.join(['%s=%s' % (k, v) for k, v in self._root.current_dirs.items()])
            commands.insert(0, 'set.dir(%s)' % current_dirs)
        commands.append('get.current()')

        # TODO: check that logfile name does not already exist
        random.seed()
        rn = random.randint(10000, 99999)
        logfile = 'mothur.ipython.%d.logfile' % rn
        commands.insert(0, 'set.logfile(name=%s)' % logfile)

        # format commands for mothur execution
        commands_str = '; '.join(commands)

        # run mothur command in command line mode
        return_code = call(['mothur', '#%s' % commands_str])

        if self._root.parse_log_file:
            current_files, dirs = self._parse_output(logfile)

        if self._root.display_output:
            self._display_output(base_command, logfile)

        self._root.return_code = return_code
        self._root.current_files = current_files
        self._root.current_dirs = dirs

        return self._root

        # print('CALLED: {}(args={}, kwargs={})'.format(self.name, repr(args), repr(kwargs)))

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

    @staticmethod
    def _display_output(command, logfile):
        """
        Prints contents of logfile.
        
        :param commands: mothur commands
        :type commands: list
        :param logfile: path of the output logfile generated by mothur
        :param logfile: str
        
        """

        # match = 'mothur > {}'.format(command)
        match = command
        # print('match: ', match)
        # print('logfile: ', logfile)

        with open(logfile, 'r') as log:
            lines = log.readlines()

            # for line in lines:
            #     print('-----')
            #     print('line: ', line)
            #     print('match: ', match)
            #     print(match in line)


            # print(lines)
            #
            # find first instance of set.current in the logfile
            start_idx = next(idx for idx, line in enumerate(lines) if match in line)

            # find length of file
            # TODO: do this more efficiently
            file_len = len(lines[start_idx:])

            # TODO uncomment this when adding saving current
            # find last instance of get.current in the logfile
            # TODO: do this more efficiently
            last_idx = next(idx for idx, line in enumerate(lines[:start_idx:-1]) if 'get.current' in line)
            output_end = (file_len - last_idx) - 1

            for idx, line in enumerate(lines[start_idx:]):
                if idx > 1000 or idx >= output_end:
                    break
                print(line.strip())

        return