import requests
import tempfile
import os
import zipfile
import shutil

def makesite_local(tpl_path: str, sitemap, repo="https://raw.githubusercontent.com/raffazizzi/", output="tei", copy=False):
  if copy:
    copy_dest = os.path.join(tempfile.gettempdir(), os.path.basename(tpl_path))
    if os.path.exists(copy_dest) and os.path.isdir(copy_dest):
      shutil.rmtree(copy_dest)
    shutil.copytree(tpl_path, copy_dest,
      ignore = shutil.ignore_patterns(".git"))
    tpl_path = copy_dest

  # Get templates
  tpl_cetei_path = os.path.join(tpl_path, "assets/tpl-cetei.html")
  tpl_cetei = ""
  with open(tpl_cetei_path) as tpl:
    tpl_cetei = tpl.read()

  tpl_entry_path = os.path.join(tpl_path, "assets/tpl-toc-entry.html")
  tpl_entry = ""
  with open(tpl_entry_path) as tpl:
    tpl_entry = tpl.read()

  tpl_book_path = os.path.join(tpl_path, "assets/tpl-toc-book.html")
  tpl_book = ""
  with open(tpl_book_path) as tpl:
    tpl_book = tpl.read()

  tpl_auth_path = os.path.join(tpl_path, "assets/tpl-toc-auth.html")
  tpl_auth = ""
  with open(tpl_auth_path) as tpl:
    tpl_auth = tpl.read()

  # Make TOC
  auth_content = ""
  for auth in sitemap["authors"]:
    auth_content += tpl_auth.replace(r"{auth}", auth["name"])

    book_content = ""
    for book in auth["books"]:
      book_content += tpl_book.replace(r"{book}", book["title"])

      entries = ""

      for file in book["files"]:
        filename = file["filename"]

        # Add entry
        repodir = sitemap["group"] + "/tei/" + auth["id"] + "/" + book["id"]
        tei_url = f"{repo}/{repodir}/{filename}.xml"
        md_url = "https://raw.githubusercontent.com/OpenITI/" + sitemap["group"] + "/master/data/" + auth["id"] + "/" + book["id"] + "/" + filename
        entry = tpl_entry.replace(r"{filename}", filename)
        entry = entry.replace(r"{title}", file["title"])
        entry = entry.replace(r"{uri}", file["version"])
        entry = entry.replace(r"{tei_url}", tei_url)
        entry = entry.replace(r"{md_url}", md_url)
        entries += entry

        dirname = os.path.join(tpl_path, filename)
        os.mkdir(dirname)
        cetei = tpl_cetei.replace(r"{tei_filename}", tei_url)
        cetei = cetei.replace(r"{title}", file["title"])
        with open(os.path.join(dirname, "index.html"), "w") as index:
            index.write(cetei)

      book_content = book_content.replace(r"{entries}", entries)
    auth_content = auth_content.replace(r"{books}", book_content)

  with open(os.path.join(tpl_path, "index.html"), "r") as index:
    contents = index.read()
    contents = contents.replace(r"{group}", sitemap["group"])
    contents = contents.replace(r"{toc}", auth_content)
    with open(os.path.join(tpl_path, "index.html"), "w") as index_w:
      index_w.write(contents)

  return tpl_path

def makesite(sitemap, url="https://github.com/OpenITI/openiti-teicorpus-site-template/archive/simple.zip", output="tei"):
  response = requests.get(url)
  tmp = tempfile.gettempdir()
  dest = os.path.join(tmp, "openiti-site-template.zip")
  open(dest, "wb").write(response.content)

  with zipfile.ZipFile(dest, 'r') as z:
    z.extractall(tmp)
  
  return makesite_local(os.path.join(tmp, "openiti-teicorpus-site-template-main"), sitemap, output)
