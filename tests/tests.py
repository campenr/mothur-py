import os
import unittest
from shutil import rmtree

from mothur_py.core import Mothur


class Test(unittest.TestCase):

    def reset_current(self):
        """Rests current files and dirs to initial state."""

        self.mothur.current_files = dict()
        self.mothur.current_dirs = dict()

        self.mothur.current_dirs['input'] = self.test_input_dir
        self.mothur.current_dirs['output'] = self.test_output_dir

        return

    def setUp(self):
        """Sets up testing variables."""

        self.mothur = Mothur()
        self.mothur.suppress_logfile = True
        self.mothur.verbosity = 0

        # setup directories for testing
        test_dir = os.path.join(os.getcwd(), 'tests')
        self.test_output_dir = os.path.join(test_dir, 'test_output')
        if not os.path.isdir(self.test_output_dir):
            os.makedirs(self.test_output_dir)
        self.test_input_dir = os.path.join(test_dir, 'test_data')

        return

    def test_singular_func(self):
        """Test running a function from mothur that has only one word."""

        # reset current files/dirs manually to avoid issue with help() if there are current dirs set
        self.mothur.current_files = dict()
        self.mothur.current_dirs = dict()

        self.mothur.help()

        return

    def test_dual_func(self):
        """
        Test running a function from mothur that has two words.
        
        Also tests whether passing named paramter works.
        
        """

        # reset current files/dirs
        self.reset_current()

        self.mothur.summary.seqs(fasta='test_fasta_1.fasta')

        return

    def test_unnamed_parameter(self):
        """Test running a function with an unnamed parameter."""

        # reset current files/dirs manually to avoid issue with help() if there are current dirs set
        self.mothur.current_files = dict()
        self.mothur.current_dirs = dict()

        self.mothur.help('summary.seqs')

        return


    def test_mothur_error_1(self):
        """Test that when mothur errors with invalid command python errors as well."""

        # reset current files/dirs
        self.reset_current()

        with self.assertRaises(RuntimeError):
            self.mothur.invalid.command()

        return

    def test_mothur_error_2(self):
        """Test that when mothur errors with bad command arguments python errors as well."""

        # reset current files/dirs
        self.reset_current()

        with self.assertRaises(RuntimeError):
            self.mothur.summary.seqs()

        return

    def tearDown(self):
        """Cleans up testing environment."""

        rmtree(self.test_output_dir)

        return


if __name__ == '__main__':
    unittest.main()
