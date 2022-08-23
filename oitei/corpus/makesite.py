import requests
import tempfile
import os
import zipfile
import json

def makesite_local(tpl_path: str, sitemap, output="tei"):
  os.mkdir(os.path.join(tpl_path, "static"))
  with open(os.path.join(tpl_path, "static/sitemap.json") , "w" ) as write:
    json.dump( sitemap , write )
  return tpl_path

def makesite(sitemap, url="https://github.com/OpenITI/openiti-teicorpus-site-template/archive/main.zip", output="tei"):
  response = requests.get(url)
  tmp = tempfile.gettempdir()
  dest = os.path.join(tmp, "openiti-site-template.zip")
  open(dest, "wb").write(response.content)

  with zipfile.ZipFile(dest, 'r') as z:
    z.extractall(tmp)
  
  return makesite_local(os.path.join(tmp, "openiti-teicorpus-site-template-main"), sitemap, output)
