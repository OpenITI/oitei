from .corpus import convert_corpus as cc

def convert_corpus(path: str, output="tei"):
  cc(path, output)


__all__ = [
  'convert_corpus',
]
