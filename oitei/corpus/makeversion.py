import re
from typing import Dict
from typing import TypedDict
from lxml import etree
from lxml.etree import Element

from oitei.tei_template import DECLS

class VersionRecord(TypedDict):
    uri: str
    extent: Element
    bibl: Element
    resp: Element
    note: Element
    date: Element

def make_version_record(yml: Dict) -> VersionRecord:
    rec: VersionRecord = {
        "uri": "",
        "extent": etree.fromstring('<extent xmlns="http://www.tei-c.org/ns/1.0"/>'),
        "bibl": etree.fromstring('<listBibl type="version" xmlns="http://www.tei-c.org/ns/1.0"/>'),
        "resp": etree.fromstring('<respStmt xmlns="http://www.tei-c.org/ns/1.0"/>'),
        "note": etree.fromstring('<encodingDesc xmlns="http://www.tei-c.org/ns/1.0"/>'),
        "date": etree.fromstring('<revisionDesc xmlns="http://www.tei-c.org/ns/1.0"/>')
    }

    for entry in yml:
        value = yml[entry]
        # URI
        if entry.startswith("00#VERS#URI######"):
            uri = value.strip()
            safeid: str
            if (re.match(r"^\d", uri)):
                safeid = f"oitei_{uri}"
            else:
                safeid = uri    
            rec["uri"] = safeid
        if re.match("00#VERS#C?LENGTH##", entry):
            measure_el = etree.SubElement(rec["extent"], "measure")
            unit = "words"
            if "CLENGTH" in entry:
                unit = "characters"
            measure_el.set("unit", unit)
            measure_el.text = value.strip()
        if re.match("80#VERS#(BASED|COLLATED|LINKS)####", entry):
            [code, v, btype, rest] = re.split("#+", entry)

            uris = value.strip().split(", ")
            if len(uris) > 0:
                for u in uris:
                    bibl_el = etree.SubElement(rec["bibl"], "bibl")
                    bibl_el.set("type", btype.lower())
                    ptr_el = etree.SubElement(bibl_el, "ptr")
                    ptr_el.set("target", u.strip())
        if entry.startswith("90#VERS#ANNOTATOR"):
            resp_el = etree.SubElement(rec["resp"], "resp")
            resp_el.text = "Annotator"
            name_el = etree.SubElement(rec["resp"], "name")
            name_el.text = value.strip()
        elif entry.startswith("90#VERS#COMMENT#"):
            p_el = etree.SubElement(rec["note"], "p")
            p_el.text = value.strip()
        elif entry.startswith("90#VERS#DATE#####"):
            change_el = etree.SubElement(rec["date"], "change")
            change_el.set("when", yml.get("90#VERS#DATE#####:").strip())
            change_el.text = "Latest change."

    return rec


def make_version_record_str(yml: Dict) -> str:
    rec = make_version_record(yml)
    el = etree.fromstring('<teiHeader xmlns="http://www.tei-c.org/ns/1.0"/>')
    fd = etree.SubElement(el, "fileDesc")
    fd.append(rec["extent"])
    el.append(rec["bibl"])
    el.append(rec["resp"])
    el.append(rec["note"])
    el.append(rec["date"])
    tree_str = etree.tostring(el, xml_declaration=False, pretty_print=True, encoding="UTF-8").decode("utf-8")
    return DECLS + tree_str
