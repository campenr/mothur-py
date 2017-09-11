from subprocess import call

class MothurFunction:
    """
    Encapsualtes Mothur function.

    """
    def __init__(self, parent, name):
        self.parent = parent
        self.name = parent.name + '.' + name

    def __getattr__(self, name):
        return MothurFunction(self, name)

    def __call__(self, *args, **kwargs):

        mothur_command = self.name.split('.', 1)[1]
        # print(mothur_command)

        # print('args: ', repr(args))
        # print('kwargs: ', repr(kwargs))

        formatted_args = ''
        formatted_kwargs = ''

        if args:
            formatted_args = ','.join(args)
        if kwargs:
            formatted_kwargs = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())

        print('formatted_kwargs: ', len(formatted_kwargs))
        print('formatted_args: ', len(formatted_args))

        mothur_args = ''
        if len(formatted_args) == 0:
            mothur_args  = formatted_kwargs
        else:
            mothur_args = formatted_args
            if len(formatted_kwargs) > 0:
                mothur_args = mothur_args + ',' + formatted_kwargs

        print(mothur_args)



        call(['mothur', '#{0}({1})'.format(mothur_command, mothur_args)])

        # print('CALLED: {}(args={}, kwargs={})'.format(self.name, repr(args), repr(kwargs)))

class Mothur:
    def __init__(self):
        self.name = '<root>'

    def __getattr__(self, name):
        return MothurFunction(mothur, name)


mothur = Mothur()
# mothur.help()
mothur.summary.shared(shared='test.shared')