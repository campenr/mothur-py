import os
import unittest
from shutil import rmtree

from mothur_py.core import Mothur


class Test(unittest.TestCase):

    def setUp(self):

        self.mothur = Mothur()
        self.mothur.suppress_logfile = True
        self.mothur.verbosity = 1

        # setup directories for testing
        self.test_output_dir = 'test_output_data'
        if not os.path.isdir(self.test_output_dir):
            os.makedirs(self.test_output_dir)
        self.mothur.current_dirs['input'] = os.getcwd()
        self.mothur.current_dirs['output'] = self.test_output_dir

    def test_singlular_func(self):
        """Test running a function from mothur that has only one word."""

        # reset current files/dirs
        self.mothur.current_files = dict()
        self.mothur.current_dirs = dict()

        self.mothur.help()

        pass

    def test_dual_func(self):
        """Test running a function from mothur that has two words."""

        # reset current files/dirs
        self.mothur.current_files = dict()
        self.mothur.current_dirs = dict()

        fasta_file = os.path.join('tests', 'test_data', 'test_fasta_1.fasta')
        self.mothur.summary.seqs(fasta=fasta_file)

        pass


    def test_mothur_error(self):
        """Test that when mothur errors python errors as well."""

        # reset current files/dirs
        self.mothur.current_files = dict()
        self.mothur.current_dirs = dict()

        with self.assertRaises(RuntimeError):
            self.mothur.summary.seqs()

    def tearDown(self):

        rmtree(self.test_output_dir, )


if __name__ == '__main__':
    unittest.main()