# oitei: OpenITI TEI Converter

This Python library converts an [OpenITI mARkdown](https://alraqmiyyat.github.io/mARkdown/) document and returns a TEI-XML string based on the [OpenITI TEI Schema](https://openiti.github.io/tei_openiti/tei_openiti.html).

## Installation

Set up a virtual environment with `venv`

```py
python3 -m venv .env
```

Activate the virtual environment

```py
source .env/bin/activate
```

Install

```py
python setup.py install
```

## Usage

```py
import oitei
md = open("markdown.md", "r").read()
md.close()
tei_string = oitei.convert(md).tostring() # or just cast to string with str()
with open('tei.xml', 'w') as writer:
    writer.write(tei_string)
```


## Coverage

This converter is based on the [OpenITI mARkdown Parser](https://openiti.github.io/oimdp/oimdp.structures.html), which covers the mARkdown specification.

The most common structures are currently converted to TEI, but other less common ones are still missing:

* MorphologicalPattern
* OpenTagAuto
* OpenTagUser
* RouteDist
* RouteFrom
* RouteTowa

There are also plans to convert to TEI YAML metadata provided with mARkdown files in the OpenITI corpus.
