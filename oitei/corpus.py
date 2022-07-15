import sys
import os
import re
import logging
from typing import List

def make_author_record(yml: List[str]) -> str:
    uri: str
    nameslist: List[str] = []
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

    for entry in yml:
        # URI
        if entry.startswith("00#AUTH#URI#"):
            uri = entry.split(":")[1].strip()
        # NAMES
        elif entry.startswith("10#AUTH#"):
            [code, a, ntype, nlang, value] = re.split("#+|:", entry)
            att = "type"
            if ntype == "KUNYA":
                att = "role"
            nameslist.append(
                f"""<name {att}="{ntype.lower()}" xml:lang="{nlang}">{value.strip()}</name>"""
            )
        # BIRTH and DEATH
        elif re.match(r"20#AUTH#(BORN|DIED)#", entry):
            [code, a, event, cal, value] = re.split("#+|:", entry)
            places_raw = value.split(",")
            places = [p.strip() for p in places_raw]
            life_event[event.lower()]["places"] = places
        elif re.match(r"30#AUTH#(BORN|DIED)#", entry):
            [code, a, event, cal, value] = re.split("#+|:", entry)
            # Skip unknown date
            if re.match(value, 'X+'):
                continue
            if cal != "AH":
                logging.warn(f"Unknown calendar in author record entry: {entry}")
            life_event[event.lower()]["calendar"] = cal
            life_event[event.lower()]["date"] = value.strip()

    # Assemble XML fragment

    def _make_event_fragment(ev_type):
        ev = life_event[ev_type]
        tag = "birth"
        if ev_type == 'died':
            tag = "death"

        evdate = ""
        if ev["date"]:
            evdate = f'when-custom="{ev["date"]}" calendar="{ev["calendar"]}"'
        evplaces = ""
        if ev["places"]:
            evplaces = f"""<placeName ref="{" ".join(ev["places"])}" />"""

        if evdate and not evplaces:
            return f"""<{tag} {evdate}/>"""
        elif evdate or evplaces:
            return f"""<{tag} {evdate}>
        {evplaces}
    </{tag}>"""
        else:
            return ""

    names = "\n        ".join(nameslist)
    persname_el = f"""<persName>
        {names}
    </persName>"""

    birth_el = _make_event_fragment("born")
    death_el = _make_event_fragment("died")

    content = "\n    ".join(filter(None, [persname_el, birth_el, death_el]))
    return f"""<person xml:id="{uri}">
    {content}    
</person>"""
    

def convert_corpus(path: str, output="tei"):
    """Given an OpenITI Corpus folder, process the books contained."""
    # Structure:
    # > data
    # > > author+
    # > > > AUTHOR METADATA
    # > > > book+
    # > > > > BOOK METADATA
    # > > > > VERSION METADATA
    # > > > > markdown text+ 
    #
    # Duplicate folder structure
    # generate author and book metadata, keeping track of:
    # * author name
    # * book title
    # Identify mARkdown file (usually no extension; could check for magic code or attempt conversion as it makes that check before starting)
    # perform oitei conversion and log issues
    # * pass on author name, book title, and ref ids to be injected at transformation time.

    if not os.path.exists(path):
        sys.exit("Path does not exist.")
    if not os.path.exists(output):
        try:
            os.mkdir(output)
        except Exception:
            raise Exception("Could not create output directory.")
    elif len(os.listdir(output)) > 0:
        sys.exit("Output directory is not empty.")

    for root, dirs, files in os.walk(path):
        # Each iteration is one folder
        print("iteration", root)
        dest = os.path.basename(root)
        output_dest = os.path.join(output, dest)
        try:
            os.mkdir(output_dest)
        except Exception:
            raise Exception(f"Could not create directory {dest}")

        for name in files:
            [filename, ext] = os.path.splitext(name)
            if ext == ".yml":
                yml_path = os.path.join(root, name)
                with open(yml_path, "r") as yml_file:
                    yml = yml_file.readlines()
                    if "00#AUTH#" in yml[0]:
                        auth = make_author_record(yml)
                        with open(os.path.join(output_dest, f"{filename}.xml"), "w") as writer:
                            writer.write(auth)
                    elif "00#BOOK#" in yml[0]:
                        print("book file")
                    elif "00#VERS#" in yml[0]:
                        print("version file")
                    else:
                        logging.warning(f"Could not determine type of metadata file: {yml_path}")

convert_corpus("../OpenITI-Corpus/0575AH/data/0552CalaUsmandi")