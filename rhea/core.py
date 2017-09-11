from subprocess import call


class Mothur:
    """
    Main class that contains configuration for Mothur execution and catches Mothur function calls.
    
    """

    def __init__(self, name='mothur'):
        self.name = name

    def __getattr__(self, name):
        """Catches unknown method calls to run them as Mothur functions instead."""
        return MothurFunction(self, self, name)


class MothurFunction:
    """
    Callable handler for Mothur function calls generated from unknown method calls for `Mothur`.
    
    ..note:: This class will call itself iteratively if passed an attribute until it is passed a callable
    at which point it with format the function call for Mothur and execute it using Mothur's batch mode.

    """
    def __init__(self, root, parent, name):
        """
        Instantiates a MothurFunction instance.
        
        :param root: the object at the root of the Mothur and MothurFunction tree
        :param parent: the object that created this class instance
        :param name: the name of this class instance
        :type root: rhea.core.Mothur
        :type parent: rhea.core.Mothur or rhea.core.MothurFunction
        :type name: str
        
        """

        self.root = root
        self.parent = parent
        self.name = parent.name + '.' + name

    def __getattr__(self, name):
        """
        Creates a child MothurFunction object.
        
        :param name: the name of the attribute being requested by the calling function/class
        :type name: str
        
        :return: a new MothurFunction instance with self.parent set to this MothurFunction instance.
        :returns: rhea.core.MothurFunction
        
        """

        return MothurFunction(self.root, self, name)

    def __call__(self, *args, **kwargs):
        """
        Catches method calls and formats and executes them as commands within Mothur.
                
        """

        # extract name of Mothur command
        mothur_command = self.name.split('.', 1)[1]

        # get and format arguments for mothur command call
        formatted_args = ''
        formatted_kwargs = ''

        if args:
            formatted_args = ','.join(args)
        if kwargs:
            formatted_kwargs = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())

        mothur_args = ''
        if len(formatted_args) == 0:
            mothur_args  = formatted_kwargs
        else:
            mothur_args = formatted_args
            if len(formatted_kwargs) > 0:
                mothur_args = mothur_args + ',' + formatted_kwargs

        print(mothur_args)

        # TODO rather than return return code, capture output and format for display and dicitonary like access of output files
        # execute Mothur command using batch mode and capture and return the return code
        return_code = call(['mothur', '#{0}({1})'.format(mothur_command, mothur_args)])
        return return_code

        # print('CALLED: {}(args={}, kwargs={})'.format(self.name, repr(args), repr(kwargs)))
