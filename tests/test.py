import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import unittest
import oitei


class TestStringMethods(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestStringMethods, self).__init__(*args, **kwargs)
        root = os.path.dirname(__file__)
        filepath = os.path.join(
            root, "test.md"
        )
        test_file = open(filepath, "r")
        self.text = test_file.read()
        test_file.close()
        self.converted = oitei.convert(self.text)
        with open('test.xml', 'w') as writer:
            writer.write(str(self.converted))

    def test_magic(self):
        self.assertEqual(True, True)


if __name__ == "__main__":
    unittest.main()
