import unittest
import os
from shutil import rmtree
from rhea import Mothur


class Test(unittest.TestCase):

    def setUp(self):

        self.mothur = Mothur()
        self.mothur.suppress_logfile = True
        self.mothur.verbosity = 0

        # setup directories for testing
        self.test_output_dir = 'test_output_data'
        if not os.path.isdir(self.test_output_dir):
            os.makedirs(self.test_output_dir)
        self.mothur.current_dirs['input'] = os.getcwd()
        self.mothur.current_dirs['output'] = self.test_output_dir

    def test_singlular_func(self):
        """Test running a function from mothur that has only one word."""

        self.mothur.help()

        pass

    def test_dual_func(self):
        """Test running a function from mothur that has two words."""

        fasta_file = os.path.join('test_data', 'test_fasta_1.fasta')
        self.mothur.summary.seqs(fasta=fasta_file)

        pass

    def tearDown(self):

        rmtree(self.test_output_dir)


if __name__ == '__main__':
    unittest.main()
