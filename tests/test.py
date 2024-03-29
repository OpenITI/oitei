import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import unittest
import oitei
from oitei.corpus import convert_corpus


class TestStringMethods(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestStringMethods, self).__init__(*args, **kwargs)

    def test_generic(self):
        root = os.path.dirname(__file__)
        filepath = os.path.join(
            root, "test.md"
        )
        test_file = open(filepath, "r")
        self.text = test_file.read()
        test_file.close()
        self.converted = oitei.convert(self.text).tostring()
        with open(os.path.join(root, "test.xml"), 'w') as writer:
            writer.write(self.converted)
    
    # def test_corpus_single(self):
    #     root = os.path.dirname(__file__)
    #     filepath = os.path.join(
    #         root, "../../OpenITI-Corpus/0575AH/data/0562Samcani/0562Samcani.Tahbir/0562Samcani.Tahbir.Shamela0001694-ara1.completed"
    #     )
    #     test_file = open(filepath, "r")
    #     self.text = test_file.read()
    #     test_file.close()
    #     self.converted = oitei.convert(self.text).tostring()
    #     with open(os.path.join(root, "single.xml"), 'w') as writer:
    #         writer.write(self.converted)
        

    def test_corpus(self):
        convert_corpus("../OpenITI-Corpus/0575AH/data/0562Samcani/0562Samcani.Tahbir")

    # def test_ernst(self):
    #     root = os.path.dirname(__file__)
    #     filepath = os.path.join(
    #         root, "ernst_jogiyan_markdown"
    #     )
    #     test_file = open(filepath, "r")
    #     self.text = test_file.read()
    #     test_file.close()
    #     self.converted = oitei.convert(self.text).tostring()
    #     self.converted = self.converted.replace('&lt;', '<')
    #     self.converted = self.converted.replace('&gt;', '>')
    #     with open(os.path.join(root, "ernst_jogiyan_markdown.xml"), 'w') as writer:
    #         writer.write(self.converted)


if __name__ == "__main__":
    unittest.main()
