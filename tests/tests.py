import unittest
import numpy as np
import pandas as pd

from scipy.spatial.distance import squareform, pdist

from rhea import Mothur

class Test(unittest.TestCase):

    def setUp(self):

        self.mothur = Mothur()

    def test_singlular_func(self):
        """Test running a funciton from mothur that has only one word."""

        self.mothur.help()

        pass


if __name__ == '__main__':
    unittest.main()