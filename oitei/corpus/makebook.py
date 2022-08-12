import re
import logging
from typing import Dict
from lxml import etree
from lxml.etree import Element

from oitei.tei_template import DECLS
from oitei.namespaces import XMLNS

logger = logging.getLogger(__name__)

def make_book_record(yml: Dict) -> Element:
    listBibl_el = etree.fromstring('<listBibl xmlns="http://www.tei-c.org/ns/1.0"/>')
    bibl_el = etree.SubElement(listBibl_el, "bibl")

    book_id: str

    for entry in yml:
        value = yml[entry]
        # URI / BOOK ID
        if entry.startswith("00#BOOK#URI#"):
            uri = value.strip()
            safeid: str
            if (re.match(r"^\d", uri)):
                safeid = f"oitei_{uri}"
            else:
                safeid = uri
            book_id = safeid

        # GENRES
        elif entry.startswith("10#BOOK#GENRES#"):
            bibl_el.set("ana", value.strip().replace(",", ""))
        # TITLES

        elif re.match(r"10#BOOK#TITLE(\w)#", entry):
            [code, b, level, lang] = re.split("#+", entry)
            title_type = "alt"
            if level == "TITLEA":
                title_type = "main"
            
            title_el = etree.SubElement(bibl_el, "title")
            title_el.set("type", title_type)
            title_el.text = value.strip()

            if lang:
                title_el.set(f"{XMLNS}lang", lang[:-1].lower())

        # LOCATION
        elif entry.startswith("20#BOOK#WROTE#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                for u in uris:
                    el = etree.SubElement(bibl_el, "placeName")
                    el.set("ref", u.strip())

        # DATE
        elif entry.startswith("30#BOOK#WROTE#"):
            cal = re.split("#+", entry)[-1][:-1]
            # Skip unknown date
            if re.match(value, 'X+'):
                continue
            if cal != "AH":
                logger.warn(f"Unknown calendar in author record entry: {entry}")
            date_el = etree.SubElement(bibl_el, "date")
            date_el.text = value.strip()

        # RELATED WORKS
        elif entry.startswith("40#BOOK#RELATED#"):
            # https://github.com/openiti/book_relations
            # skip template as it messes with actual regex
            if "URI of a book from OpenITI, or [Author's Title]" in value:
                continue
            relations = value.split(';')
            for relation in relations:
                parts = re.match(r"([^\()]+)\((.*?)\)", relation)
                if parts:
                    [ref, types] = parts.groups()
                    for t in types.split(", "):
                        rel_el = etree.SubElement(bibl_el, "relatedItem")
                        if "[" in ref:
                            b = etree.SubElement(rel_el, "bibl")
                            b.text = ref.strip()
                        else:
                            rel_el.set("target", f"#{ref.strip()}")
                        [main, sub] = t.strip().split(".")
                        rel_el.set("type", main)
                        rel_el.set("subtype", sub)
                else:
                    logger.warn(f"Could not parse book relation for book {book_id}")

        # EXTERNAL RELATED ITEMS
        elif re.match(r"80#BOOK#(EDITIONS|LINKS|MSS|STUDIES|TRANSLAT)#", entry):
            rel = re.split("#+", entry)[2]
            for r in value.strip().split(", "):
                el = etree.SubElement(bibl_el, "relatedItem")
                el.set("type", rel.lower())
                el.set("target", r)

        # COMMENT 
        elif entry.startswith("90#BOOK#COMMENT#"):
            etree.SubElement(bibl_el, "note").text = value.strip()


    bibl_el.set(f"{XMLNS}id", book_id)

    return listBibl_el


def make_book_record_str(yml: Dict) -> str:
    el = make_book_record(yml)
    tree_str = etree.tostring(el, xml_declaration=False, pretty_print=True, encoding="UTF-8").decode("utf-8")
    return DECLS + tree_str
