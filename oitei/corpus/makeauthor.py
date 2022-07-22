import re
import logging
from typing import List
from lxml import etree
from yaml import YAMLObject

from oitei.tei_template import DECLS
from oitei.namespaces import NS, XMLNS, TEINS

def make_author_record(yml: YAMLObject) -> str:
    doc = etree.fromstring('<person xmlns="http://www.tei-c.org/ns/1.0"/>')
    uri: str
    life_event = {
        "born": {
            "date": "",
            "calendar": "",
            "places": [],
        },
        "died": {
            "date": "",
            "calendar": "",
            "places": [],
        }
    }
    visited = ""

    def _get_event_el(ev_type):
        tag = "birth"
        if ev_type == 'DIED':
            tag = "death"
        ev_el = doc.find(f".//{tag}", NS)
        if not ev_el:
            ev_el = etree.SubElement(doc, tag)
        return ev_el

    for entry in yml:
        value = yml[entry]
        # URI
        if entry.startswith("00#AUTH#URI#"):
            uri = value.strip()

        # NAMES
        elif entry.startswith("10#AUTH#"):
            # Find or create persName
            persname_el = doc.find(".//persName", NS)
            if not persname_el:
                persname_el = etree.SubElement(doc, "persName")

            # Parse entry
            [code, a, ntype, nlang] = re.split("#+", entry)
            att = "type"
            if ntype == "KUNYA":
                att = "role"
            name_el = etree.SubElement(persname_el, "name")
            name_el.set(att, ntype.lower())
            name_el.set(f"{XMLNS}lang", nlang.lower())
            name_el.text = value.strip()

        # BIRTH and DEATH
        elif re.match(r"20#AUTH#(BORN|DIED)#", entry):
            [code, a, event, lang] = re.split("#+", entry)
            places = value.split(",")

            ev_el = _get_event_el(event)
            for place in places:
                place_el = etree.SubElement(ev_el, "placeName")
                place_el.set("ref", place.strip())

        elif re.match(r"30#AUTH#(BORN|DIED)#", entry):
            [code, a, event, cal] = re.split("#+", entry)
            # Skip unknown date
            if re.match(value, 'X+'):
                continue
            if cal != "AH":
                logging.warn(f"Unknown calendar in author record entry: {entry}")
            
            ev_el = _get_event_el(event)
            ev_el.set("calendar", f"#{cal.lower()}")
            ev_el.set("date", value.strip())

        # PLACES VISITED
        elif entry.startswith("20#AUTH#VISITED#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                el = etree.SubElement(doc, "listEvent")
                for u in uris:
                    ev_el = etree.SubElement(el, "event")
                    ev_el.set("type", "visit")
                    ev_el.set("where", u.strip())

        # RESIDENCES
        elif entry.startswith("20#AUTH#RESIDED#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                for u in uris:
                    res_el = etree.SubElement(doc, "residence")
                    place_el = etree.SubElement(res_el, "placeName")
                    place_el.set("ref", u.strip())

        # BIBLIOGRAPHY
        elif entry.startswith("80#AUTH#BIBLIO#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                el = etree.SubElement(doc, "listBibl")
                for u in uris:
                    b_el = etree.SubElement(el, "bibl")
                    b_el.set("ref", u.strip())

        # COMMENT 
        elif entry.startswith("90#AUTH#COMMENT#"):
            etree.SubElement(doc, "note").text = value.strip()


    doc.set(f"{XMLNS}id", uri)

    tree_str = etree.tostring(doc, xml_declaration=False, pretty_print=True, encoding="UTF-8").decode("utf-8")
    return DECLS + tree_str