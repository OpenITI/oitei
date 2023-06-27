from .converter import Converter
from .converter import Metadata

def convert(text: str, metadata: Metadata = None):
    """Convert to TEI from a mARkdown string"""
    C = Converter(text, metadata)
    C.convert()

    return C

__all__ = [
   'convert',
]
__version__ = '1.1.1'
