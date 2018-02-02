# mothur-py

Copyright &#169; 2018, Richard Campen. All rights reserved.

See LICENSE.txt for full license conditions.

---

### Description

A python wrapper for the command line version of the bioinformatics tool 
[mothur](https://www.mothur.org/).

See the change log at the end of this ReadMe for a full list of changes.

Mothur-py was inspired by the [ipython-mothurmagic](https://github.com/SchlossLab/ipython-mothurmagic) module, but with an
intention to provide a more general python wrapper that would work outside of the IPython/Jupyter notebook environment, 
as well as provide support for mothur's `current` keyword functionality.

**Note:** This module has only been tested with mothur v1.39.5 and python 3. It should in theory work with older 
versions of mothur, but the older the version the less likely as this module relies upon some of the more recent mothur 
commands/output to function properly.

---

### Installation

To install the latest release version you can just `pip install mothur-py`. To install the most up to date code you should
download/clone this repository and create a binary distribution using `python setup.py bdist_wheel` that will create a .whl file
in the `dist` folder. You can then install mothur-py with pip from the .whl file using `pip install <wheel_file_name>`. The
advantage of this method over just running `python setup.py install` is that you can easily remove or update the package via pip.

---

### Basic Usage

**NOTE:** mothur-py expects mothur to be installed in the users PATH environment variable. If this is not the case you
will need to tell it where to find the mothur executable. See the configuration section of the README for details.

Use of this module revolves around the `Mothur` class that catches method calls and passes them off to mothur to be run 
as commands. An instance of the `Mothur` class needs to be created before running any commands:

    # create instance of Mothur class
    from mothur_py import Mothur
    m = Mothur()
    
Commands in mothur can then be executed as methods of the `Mothur` class instance using the same names you would use 
within the command line version of mothur:

    # run the mothur help command
    m.help()

Command parameters can either be passed as python native types (i.e. strings, integers, floats, booleans, lists) *or* as
strings that match the format that mothur would expect:

    # running make contigs using str input for file parameter, and int for processor paramenter
    m.make.contigs(file='basic_usage.files', processors=2)

    # running summary.single, passing calculators as mothur formatted list
    m.summary.single(shared='basic_usage.shared', calc='nseqs-sobs-coverage-shannon-simpson')

    # running summary.single, passing calculators as python list also works
    m.summary.single(shared='basic_usage.shared', calc=['nseqs', 'sobs', 'coverage', 'shannon', 'simpson'])

The `Mothur` object saves a record of the current directories and files and the output files from mothur after executing each command.
These are stored as dictionary attributes of the `Mothur` object:

    # run a command
    m.summary.seqs(fasta='basic_usage.fasta')
    
    # display current mothur files
    print(m.current_files)

    # read in the output file from summary.seqs()
    with open(m.output_files['summary'][0], 'r') as in_handle:
        in_handle.read()

**NOTE:** Due to the possibility of multiple output files with the same extension the output files are saved as lists within the attribute
dictionaries with the file extension as the key. This issue does not occur for current files and dirs so they are stored as the actual
values, not as lists of the values, with the key being the type of file according to mothur (usually the same as the file extension).

**NOTE:** Each successive execution of a mothur command will update the current files and dirs, but will completely overwrite the saved output
files. This is so that you have access to the current files generated more than one command ago, but do not get access to output from more than
one command ago, which would be confusing.

There is also implementation of the `current` keyword used in the command line version of mothur:
       
    # run the mothur summary.seqs command using the 'current' option
    # NOTE: current is being passed as a string
    m.summary.seqs(fasta='current')
     
    # like the command line version, you don't even need to specify 
    # the 'current' keyword for some commands
    m.summary.seqs() 
    
Behind the scenes, the `current` keyword is enabled by appending the users command with the `get.current()` command to 
list the current directories and files being used by mothur, parsing of the output to extract this information, and 
prepending future commands with `set.dir()` and `set.current()` to tell mothur what these should be. This is necessary 
as each call to mothur is executed as a separate mothur session and therefore mothur can not store this information 
itself.

---

### Configuration 
    
The `Mothur` class stores configuration options for how mothur is executed. These options include `mothur_path` to tell
mothur-py where to find the mothur executable, `verbosity` to control how much output there is, `mothur_seed` to control 
the seed used by mothur for random number generation, `logfile_name` to set the name of the mothur logfile, and 
`suppress_logfile` which suppresses the creation of the mothur logfile.

The default for `mothur_path` is `mothur` which will only work if mothur is in your PATH environment variable.
If it is not then you will need to specify where to find the mothur executable, including the name of the executable 
itself:

    # configure mothur with executable in current directory on Windows
    m = Mothur(mothur_path='mothur.exe')
    
    # configure mothur with executable in current directory on Linux
    m = Mothur(mothur_path='./mothur')
    
    # configure mothur with executable in alternate directory on Windows
    m = Mothur(mothur_path='\\path\\to\\mothur.exe')
    
Failure to correctly configure the `mothur_path` will usually result in a PermissionError:

    m = Mothur(mothur_path='/not/a/real/path/to/mothur')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File ".../mothur_py/core.py", line 199, in __call__
        p = Popen([self.root_object.mothur_path, '#%s' % commands_str], stdout=PIPE, stderr=STDOUT)
      File "/usr/lib/python3.5/subprocess.py", line 947, in __init__
        restore_signals, start_new_session)
      File "/usr/lib/python3.5/subprocess.py", line 1551, in _execute_child
        raise child_exception_type(errno_num, err_msg)
    PermissionError: [Errno 13] Permission denied

When `verbosity` is set to `0` there is no output printed, `1` prints the normal output as would be seen with command 
line execution (minus the header that contains the mothur version and runtime information), and `2` displays all output
including the commands being executed behind the scenes to enable the `current` keyword to work. The default option is 
`0`, with `1` being useful when you want to see the standard mothur output, and `2` being useful for debugging purposes. 

If `mothur_seed` is set to a valid integer then this number will be passed to mothur to be used for random number
generation. This is implemented by adding the `seed=<your seed here>` named parameter to each mothur command. Not all 
commands will accept having a seed set. For these commands you may need to set the `mothur_seed` parameter to `None`
for the execution of that command, e.g.:
 
    m = Mothur(mothur_seed=12345)
    
    # summary.seqs() allows setting the seed so this will run fine
    m.summary.seqs(fasta='current')
    
    # help() does not accept having the seed set so need to alter that value temporarily, otherwise an error will occur
    seed = m.mothur_seed
    m.mothur_seed = None
    m.help()
    m.mothur_seed = seed
    
The `logfile_name` option allows the user to specify the name that the mothur logfile will have. As the logfile can be 
appended to a single logfile can store the record of all operations related to a single Mothur object.

**Note:** When copying mothur objects it is important to then specify different logfiles for them otherwise they
may attempt to use the same logfile. Additionally, if `suppress_logfile` is true, the logfile will be suppressed even
if it has been given a name by the user.

The `supress_logfile` option is useful when you don't want the log files, such as when running in an Jupyter (nee 
IPython) notebook with `verbosity=1`, in which case you already have a record of mothur's output and the mothur logfiles
are superfluous.

**Note:** Currently, due to the way that mothur creates the logfiles, a logfile will always be created BUT it will be 
cleaned up upon successful execution if `suppress_logfile=True`. However, if mothur fails to successfully execute, i.e. 
execution hangs or is interrupted, the logfile will not be cleaned up. For relevant discussion of this behaviour in 
mothur see [here](https://github.com/mothur/mothur/issues/281) and [here](https://github.com/mothur/mothur/issues/377).

You can also instantiate the `Mothur` object with your desired configuration options.

    m = Mothur(verbosity=1, mothur_seed=543210, suppress_logfile=True)
    
---

### Advanced Usage

The current files and current directories for use in mothur are stored in dictionary attributes of the `Mothur` 
instance, `current_files` and `current_dirs` respectively. These values can be passed to mothur commands, e.g:

    # passing current fasta file to summary.seqs()
    m.summary.seqs(fasta=m.current_files['fasta'])
       
The `current` keyword is actually just a shortcut for this functionality so it will always be easier to just pass 
`'current'`. However, this demonstrates that the parameters of the mothur commands can accept any variable as long as it 
will resolve to something that mothur accepts. In the above example, the dictionary value resolves to a string that is
the path to the `.fasta` file. As a better example of passing python variables as mothur command parameters, you could 
perform classification of sequences at multiple defined cutoffs as follows:

    from copy import deepcopy
    
    # init results container
    mothur_objs = dict()

    # iterate over list off possible cutoff values
    for cutoff in [70, 80, 90]:
    
        # make a copy of the original mothur object so we do not make unwanted modifications to the original
        m_copy = deepcopy(m)
       
        # save outputs to different folders, but keep input the same
        output_dir = 'cutoff_%s' % cutoff
        m_copy.set.dir(output=output_dir, input='.')
        m_copy.classify.seqs(fasta='current', count='current', reference='reference.fasta', taxonomy='referenece.tax',
        cutoff=cutoff)
        
        # save to results container
        mothur_objs[cutoff] = m_copy
        
This may be a convoluted example, but it demonstrates the functionality well. One note of caution with this approach is 
that depending on the mothur command and the parameter you are changing, you may be overwriting your output files as you 
go. This is the reason for saving each output to a different folder in the above example. We also create multiple copies
of the original mothur object and use those for the command instead so we can continue to use the `current` keyword
downstream and have it refer to the correct files:

    # using the results container from above
    for m_ in mothur_objs.values():
        
        # run remove.lineage() on each mothur object created previously to remove unwanted taxa
        # because we saved each classify.seqs command to a different mothur object we can safely use the 'current'
        # keyword here and know that it refers to the correct file
        m_.remove.lineage(fasta='current', count='current', taxonomy='current, taxon='unknown')
    

You can also instantiate a `Mothur` instance with predefined current file and directory dictionaries:

    m = Mothur(current_files=my_predefined_files_dict, current_dirs=my_predefined_files_dict)

This can be convenient for saving and loading the state of a mothur object to/from file as such:

    import json

    # save state of mothur object, m, to json file
    with open('mothur_object.json', 'w') as out_handle:
        json.dump(vars(m), out_handle)

    # can reload mothur object from the json file
    with open('mothur_object.json', 'r') as in_handle:
        m = Mothur(**json.load(in_handle))

---

### Change Log

#### *v0.3.1*

New features:
* Allow setting the name of the mothur logfile via configuration of the Mothur object

Bug fixes:
* Changed strings to match to detect errors and warnings from mothur in stdout
* Now check both top level and output directories when removing logfile

#### *v0.3.0*

Changes:
* The `output_files` attribute now stores the full file path for each output file, rather than just the file name as was done previously.

#### *v0.2.5*

New features:
* Added configuration option for path to the mothur executable, thereby adding support for any mothur executable location 
  (previously mothur had to be in users PATH environment variable).

#### *v0.2.4*

New features:
* Enabled passing python native types as command parameters, which are then converted to mothur compatible types as needed
* Added parsing and saving of the output files generated by the last run mothur command
* Improved documentation and examples

#### *v0.2.3*

Bug fixes:
* Fixed current files not being saved correctly to the mothur obejct after execution

#### *v0.2.2*

Changes:
* No longer return the mothur object. If it is desired to store the altered object as a copy then the deepcopy function in the copy package should be used

Bug fixes:
* Fixed verbosity level affecting the parsing of current files/dirs from stdout
* Only update the current files/dirs for the mothur object once execution of mothur ends successfully
* Fixed calls to unimplemented dunder methods (i.e. __deepcopy__) being parsed as mothur commands

New features:
* Can set the seed that mothur uses for its random number generation
* Added more unittests

#### *v0.2.1*

Bug fixes:
* Fixed bug where python failed to raise an error if mothur did

New features:
* Use of an invalid command now raises an error in python, halting execution. Previously this would fail silently.

#### *v0.2.0*

Changes:
* Renamed project from Rhea to mothur_py to avoid confusion with the R package for 16S amplicon analysis. Mothur class 
now needs to be imported from mothur_py instead.
