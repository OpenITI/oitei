import re
import logging
import string
from tkinter import E
from lxml import etree
from yaml import YAMLObject

from oitei.tei_template import DECLS
from oitei.namespaces import NS, XMLNS, TEINS

def make_author_record(yml: YAMLObject) -> str:
    listPerson_el = etree.fromstring('<listPerson xmlns="http://www.tei-c.org/ns/1.0"/>')
    person_el = etree.SubElement(listPerson_el, "person")
    listRelation_el = etree.SubElement(listPerson_el, "listRelation")

    author_id: str

    def _get_event_el(ev_type):
        tag = "birth"
        if ev_type == 'DIED':
            tag = "death"
        ev_el = person_el.find(f".//{tag}", NS)
        if ev_el is None:
            ev_el = etree.SubElement(person_el, tag)
        return ev_el

    for entry in yml:
        value = yml[entry]
        # URI / AUTHOR ID
        if entry.startswith("00#AUTH#URI#"):
            uri = value.strip()
            safeid: string
            if (re.match(r"^\d", uri)):
                safeid = f"oitei_{uri}"
            else:
                safeid = uri
            author_id = safeid

        # NAMES
        elif entry.startswith("10#AUTH#"):
            # Find or create persName
            persname_el = person_el.find(".//persName", NS)
            if persname_el is None:
                persname_el = etree.SubElement(person_el, "persName")

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
            ev_el.set("when-custom", value.strip())            

        # PLACES VISITED
        elif entry.startswith("20#AUTH#VISITED#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                el = etree.SubElement(person_el, "listEvent")
                for u in uris:
                    ev_el = etree.SubElement(el, "event")
                    ev_el.set("type", "visit")
                    ev_el.set("where", u.strip())
                    etree.SubElement(ev_el, "p")

        # RESIDENCES
        elif entry.startswith("20#AUTH#RESIDED#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                for u in uris:
                    res_el = etree.SubElement(person_el, "residence")
                    place_el = etree.SubElement(res_el, "placeName")
                    place_el.set("ref", u.strip())

        # BIBLIOGRAPHY
        elif entry.startswith("80#AUTH#BIBLIO#"):
            uris = value.strip().split(", ")
            if len(uris) > 0:
                el = etree.SubElement(person_el, "listBibl")
                for u in uris:
                    b_el = etree.SubElement(el, "bibl")
                    ptr_el = etree.SubElement(b_el, "ptr")
                    ptr_el.set("target", u.strip())

        # COMMENT 
        elif entry.startswith("90#AUTH#COMMENT#"):
            etree.SubElement(person_el, "note").text = value.strip()
        
        # RELATIONS
        elif re.match(r"40#AUTH#(STUDENTS|TEACHERS)#", entry):
            [code, a, role, rest] = re.split("#+", entry)
            uris = value.strip().split(", ")
            if len(uris) > 0:
                for u in uris:
                    relation_el = etree.SubElement(listRelation_el, "relation")
                    relation_el.set("name", role.lower())
                    active: str
                    passive: str
                    if role == "STUDENTS":
                        active = f"#{author_id}"
                        passive = u
                    elif role == "TEACHERS":
                        active = u
                        passive = f"#{author_id}"
                    else:
                        logging.warn(f"Unknown relationship role: {role}")

                    relation_el.set("active", active)
                    relation_el.set("passive", passive)

    person_el.set(f"{XMLNS}id", author_id)

    tree_str = etree.tostring(listPerson_el, xml_declaration=False, pretty_print=True, encoding="UTF-8").decode("utf-8")
    return DECLS + tree_str
