import sys
import os
import re
import shutil
import logging
import traceback
from typing import List
from lxml.etree import Element
from lxml import etree
from .makeauthor import make_author_record_str
from .makebook import make_book_record_str
from .makeversion import make_version_record, VersionRecord
from oitei.converter import Metadata, Converter

from openiti.helper.yml import readYML, check_yml_completeness
from openiti.helper.funcs import get_all_text_files_in_folder, get_all_yml_files_in_folder

from oitei.namespaces import NS, XINS

from datetime import datetime


now = datetime.now()
date_time = now.strftime("%m-%d-%Y_%H%M%S")
LOGFILE = f"oitei-{date_time}.log"

logging.basicConfig(filename=LOGFILE, filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_nbsp(text: str) -> str:
    if text[0] == "﻿":
        return text[1:]
    return text


def add_version_record_to_tei(vr: VersionRecord, doc: Element) -> Element:
    th = doc.find(".//tei:teiHeader", NS)
    fd = th.find("./tei:fileDesc", NS)
    ts = fd.find("./tei:titleStmt", NS)
    fd.insert(fd.index(ts)+1, vr["extent"])

    ts.append(vr["resp"])

    sd = doc.find(".//tei:sourceDesc", NS)
    sd.append(vr["bibl"])

    th.insert(th.index(fd)+1, vr["note"])

    th.append(vr["date"])
    return doc


def link_metadata(auth: str, book: str, doc: Element) -> Element:
    so = etree.SubElement(doc, "standOff")
    so.append(etree.Comment("AUTHOR METADATA"))
    auth_xi = etree.SubElement(so,f"{XINS}include")
    auth_xi.set("href", f"../{auth}")

    so.append(etree.Comment("BOOK METADATA"))
    book_xi = etree.SubElement(so,f"{XINS}include")
    book_xi.set("href", f"./{book}")
    return doc


def process_author_metadata(p:str, dest: str) -> tuple[str, str, str]:
    return process_metadata(p, dest,
        "AUTH", ["10#AUTH#ISM####AR:", "10#AUTH#LAQAB##AR:"], make_author_record_str)


def process_book_metadata(p: str, dest: str) -> tuple[str, str, str]:
    return process_metadata(p, dest,
        "BOOK", ["10#BOOK#TITLEA#AR:", "10#BOOK#TITLEB#AR:"], make_book_record_str)


def process_metadata(p: str, dest: str, mtype: str, fields: List[str], fn) -> tuple[str, str]:
    yml = readYML(p, reflow=True) # NB Reflow isn't working at the moment.
    record = fn(yml)
    uri = yml.get(f"00#{mtype}#URI######:").strip()

    non_default, ark = check_yml_completeness(p)
    isDefault = len(non_default) == 0
    value = re.sub(r"^\d+", "", uri)
    if not isDefault:
        value = " ".join([yml.get(f) for f in fields])

    # Write out
    output = os.path.join(dest, os.path.basename(p)).replace(".yml", "") + ".xml"
    with open(output, "w") as writer:
        writer.write(record)

    return (uri, value, output) 


def determine_folder_structure_for_file(fp: str, output: str) -> tuple[str, str]:
    book_path = os.path.dirname(fp)
    auth_path = os.path.dirname(book_path)
    base = os.path.basename(fp)
    auth_base = os.path.basename(auth_path)

    auth_dest = os.path.join(output, auth_base)
    book_dest = os.path.join(output, auth_base, os.path.basename(book_path))

    logger.info(f"Determining directory structure for: {base}")
    if not os.path.isdir(auth_dest):
        try:
            os.mkdir(auth_dest)
        except Exception:
            msg = f"Could not create directory {auth_dest}"
            logger.critical(msg)
            raise Exception(msg)

    if not os.path.isdir(book_dest):
        try:
            os.mkdir(book_dest)
        except Exception:
            msg = f"Could not create directory {book_dest}"
            logger.critical(msg)
            raise Exception(msg)

    return (auth_dest, book_dest)


def convert_corpus(p: str, output="tei"):
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
    # Get all files
    # For each file:
    # * get metadata from inferred folder
    # * create folder structure
    # * create metadata files
    # * convert

    if not os.path.exists(p):
        sys.exit("Path to corpus does not exist.")
    if not os.path.exists(output):
        try:
            os.mkdir(output)
        except Exception:
            raise Exception("Could not create output directory.")
    elif len(os.listdir(output)) > 0:
        sys.exit("Output directory is not empty.")

    mdfiles = get_all_text_files_in_folder(p)

    for mdf in mdfiles:
        filename = os.path.basename(mdf)
        book_path = os.path.dirname(mdf)
        auth_path = os.path.dirname(book_path)

        # Determine folder structure: creates structure if needed
        auth_dest, book_dest = determine_folder_structure_for_file(mdf, output)

        # Process author metadata
        yauth_path = next(get_all_yml_files_in_folder(auth_path, "author"))
        auth_uri, author, xauth_path = process_author_metadata(yauth_path, auth_dest)

        # Process book metadata (choose the right book)
        ybook_path = next(get_all_yml_files_in_folder(book_path, "book"))
        book_uri, book, xbook_path = process_book_metadata(ybook_path, book_dest)

        # Process version metadata 
        # Choose the right file since there could be multiple versions and md files in book
        yvers_paths = get_all_yml_files_in_folder(book_path, "version")
        cleanfn = filename.replace(".inProgress", "").replace(".completed", "").replace(".mARkdown", "")
        yvers_path = [yp for yp in yvers_paths if os.path.basename(yp) == cleanfn + ".yml"]
        if len(yvers_path) > 0:
            yvers = readYML(yvers_path[0], reflow=True)
            version_record = make_version_record(yvers)
        else:
            logger.error(f"Could not locate version metadata file for: {mdf}")

        # Assemble metadata
        metadata: Metadata = {
            "prefix": "oitei",
            "auth_uri": auth_uri,
            "author": author,
            "book_uri": book_uri,
            "book": book,
            "idno": version_record["uri"]
        }

        with open(mdf) as file:
            text = file.read()
            try:
                C = Converter(cleanup_nbsp(text), metadata)
                C.convert()
                C.doc = add_version_record_to_tei(version_record, C.doc)
                C.doc = link_metadata(os.path.basename(xauth_path), os.path.basename(xbook_path), C.doc)

                # Write out
                with open(os.path.join(book_dest, f"{filename}.xml"), "w") as writer:
                    writer.write(C.tostring())
                
                logger.info(f"Converted {mdf}")
            except:
                logger.error(f"Error while processing mARkdown file {mdf}")
                logger.error(traceback.format_exc())
            
    # Copy log once done.
    shutil.copyfile(LOGFILE, os.path.join(output, LOGFILE))
