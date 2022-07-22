import sys
import os
import logging
import yaml
from .makeauthor import make_author_record
    

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
        sys.exit("Path to corpus does not exist.")
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
                    # yml = yml_file.readlines()
                    yml = yaml.safe_load(yml_file)
                    if "00#AUTH#URI######" in yml:
                        auth = make_author_record(yml)
                        with open(os.path.join(output_dest, f"{filename}.xml"), "w") as writer:
                            writer.write(auth)
                    # if "00#AUTH#" in yml[0]:
                    # elif "00#BOOK#" in yml[0]:
                    #     print("book file")
                    # elif "00#VERS#" in yml[0]:
                    #     print("version file")
                    else:
                        logging.warning(f"Could not determine type of metadata file: {yml_path}")
