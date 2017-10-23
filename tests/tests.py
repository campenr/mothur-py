import os
import unittest
from shutil import rmtree

from mothur_py.core import Mothur


class Test(unittest.TestCase):

    def set_current_dirs(self, mothur_obj):
        """Rests current files and dirs to initial state."""

        mothur_obj.current_dirs['input'] = self.test_input_dir
        mothur_obj.current_dirs['output'] = self.test_output_dir

        return

    def setUp(self):
        """Sets up testing variables."""

        # setup init variables
        self.init_vars = {
            'suppress_logfile': True,
            'verbosity': 0,
            'mothur_seed': 54321
        }

        # setup directories for testing
        test_dir = os.path.join(os.getcwd(), 'tests')
        self.test_output_dir = os.path.join(test_dir, 'test_output')
        if not os.path.isdir(self.test_output_dir):
            os.makedirs(self.test_output_dir)
        self.test_input_dir = os.path.join(test_dir, 'test_data')

        return

    def test_singular_func(self):
        """Test running a function from mothur that has only one word."""

        m = Mothur(**self.init_vars)
        m.help()

        return

    def test_dual_func(self):
        """
        Test running a function from mothur that has two words.

        Also tests whether passing named paramter works.

        """

        m = Mothur(**self.init_vars)
        self.set_current_dirs(m)
        m.summary.seqs(fasta='test_fasta_1.fasta')

        return

    def test_unnamed_parameter(self):
        """Test running a function with an unnamed parameter."""

        m = Mothur(**self.init_vars)
        m.help('summary.seqs')

        return

    def test_existing_current_files(self):
        """Test that mothur remembers current files."""

        m = Mothur(**self.init_vars)
        self.set_current_dirs(m)
        m.summary.seqs(fasta='test_fasta_1.fasta')
        m.summary.seqs()

        return

    def test_mothur_error_1(self):
        """Test that when mothur errors with invalid command python errors as well."""

        m = Mothur(**self.init_vars)
        self.set_current_dirs(m)

        with self.assertRaises(RuntimeError):
            m.invalid.command()

        return

    def test_mothur_error_2(self):
        """Test that when mothur errors with bad command arguments python errors as well."""

        m = Mothur(**self.init_vars)
        self.set_current_dirs(m)
        with self.assertRaises(RuntimeError):
            m.summary.seqs()

        return

    def test_python_bool(self):
        """Test that python bools are correctly converted into mothur compatible boolean values."""

        m = Mothur(**self.init_vars)
        self.set_current_dirs(m)
        m.pcr.seqs(fasta='test_fasta_1.fasta', start=20, keepdots=False)
        m.pcr.seqs(fasta='test_fasta_1.fasta', start=20, keepdots=True)

        return

    # def test_python_iterable(self):
    #     """Test that python iterables are correctly converted into mothur compatible lists."""
    #
    #     return


    def tearDown(self):
        """Cleans up testing environment."""

        rmtree(self.test_output_dir)

        return


if __name__ == '__main__':
    unittest.main()
