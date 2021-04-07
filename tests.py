import unittest
import random

from perform import Perform, dummy_worker


class TestPerform(unittest.TestCase):
    def setUp(self):
        self.perform = Perform()

        self.data = []
        for i in range(0, 10):
            self.data.append("{}".format(random.randint(0, 10000)))

    def test_perform(self):
        self.perform.run(5, dummy_worker, self.data)
