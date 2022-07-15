from .converter import Converter
from .converter import Metadata

def convert(text: str, metadata: Metadata = None):
    """Convert to TEI from a mARkdown string"""
    C = Converter(text, metadata)
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
