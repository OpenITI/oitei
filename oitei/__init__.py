from .converter import Converter


def convert(text: str):
    """Convert to TEI from a mARkdown string"""
    C = Converter(text)
    C.convert()

    return C

# def convert_from_document(doc):
#     """Convert to TEI from a oimdp-parsed mARkdown object"""
#     return converter(doc)


__all__ = [
   'convert',
#    'convert_from_document'
]
__version__ = '1.0.0'
