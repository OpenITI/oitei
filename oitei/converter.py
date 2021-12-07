import oimdp
from oimdp.structures import AdministrativeRegion, BioOrEvent, Content, DictionaryUnit, DoxographicalItem, Editorial, Line, Paragraph, TextPart
from lxml import etree
from lxml.etree import Element
import xml.etree.ElementTree as ET
import warnings
import re

from oitei.tei_template import TEI_TEMPLATE

NS = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace"
}


class Converter:
    """OpenITI mARkdown to OpenITI TEI converter"""
     # TODO: allow users to provide template or at least URL to schema
    def __init__(self, text: str):
        self.magic_value = "######OpenITI#"
        self.doc = etree.fromstring(TEI_TEMPLATE)
        
        try:
            self.context_node = self.doc.find(".//tei:body", NS)
            self.body = self.context_node
        except Exception:
            raise Exception("Could not initiate TEI document.") 

        try:
            self.md = oimdp.parse(text)
        except Exception:
            raise Exception("Could not parse mARkdown document.") 

        if str(self.md.magic_value) != self.magic_value:
            raise Exception("Text provided does not appear to be a valid mARkdown document.") 


    def __str__(self):

        space = "  "

        def text_indent(el, level=0, islast=False):
            """ Indent text nodes despite etree's nonesensical insistence that doing so alters data.
                (any sequence of spaces is one space in XML unless xml:space="preserve" is specified) """
            xml_space = el.get("{http://www.w3.org/XML/1998/namespace}space")
            if xml_space != "preserve":
                if str(el.tail).endswith("\n"):
                    indent = level * space
                    if islast:
                        indent = (level-1) * space
                    el.tail = el.tail + indent
                tot_children = len(el)
                if tot_children:
                    for count, child in enumerate(el):
                        text_indent(child, level+1, count+1 == tot_children)

        if self.doc:
            etree.indent(self.doc, space=space)
            text_indent(self.doc)
                    
            return etree.tostring(self.doc, xml_declaration=True, pretty_print=True, encoding="UTF-8").decode("utf-8")
        else:
            return ""


    def _appendText(self, el: Element, text: str):
        children = el.getchildren()
        if len(children) > 0:
            tail = children[-1].tail
            if tail:
                children[-1].tail = tail + text
            else:
                children[-1].tail = text
        else:
            el.text = text


    def convert(self):
        # Set up TEI document from a minimal string template
        teiHeader = self.doc.find(".//tei:teiHeader", NS)
        
        # Preserve non-machine readable data as xenodata
        if self.md.simple_metadata:
            xenoData = etree.Element("xenoData")
            xenoData.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            xenoString = "\n"
            for metadata in self.md.simple_metadata:
                xenoString += str(metadata) + "\n"
            xenoData.text = xenoString 
            teiHeader.append(xenoData)

        # Process content
        for content in self.md.content:
            # print(type(content).__name__)
            self._convertStructure(content)

    def _create_p(self):
        if self.context_node.tag != "div":
            # Locate closest div
            closest = self.context_node.xpath("ancestor::tei:div", namespaces=NS)

            if closest:
                self.context_node = closest
            else:
                # If there is no div, create one.
                self.context_node = etree.SubElement(self.body, "div")
        
        self.context_node = etree.SubElement(self.context_node, "p")

    def _convertStructure(self, content):
        """Convert an oimdp.Content object to a TEI element"""

        if isinstance(content, Paragraph):
            self._create_p()

        elif isinstance(content, Line):
            if self.context_node.tag != "p":
                warnings.warn("A mARkdown line does not seem to be in a paragraph. The converter created one anyway.")
                self._create_p()

            etree.SubElement(self.context_node, "lb")

            # Lines should contain lineparts
            if len(content.parts) > 0:
                for part in content.parts:
                    self._convertStructure(part)
                self._appendText(self.context_node, "\n")

        elif isinstance(content, TextPart):
            self._appendText(self.context_node, content.orig.strip())

        # elif isinstance(content, AdministrativeRegion):
            #TODO IN PARSER!
            
        elif isinstance(content, BioOrEvent):
            if self.context_node.tag != "body":
                # Locate closest div
                closest = self.context_node.xpath("ancestor::tei:div", namespaces=NS)

                if closest:
                    self.context_node = closest
                else:
                    # Return to body
                    self.context_node = self.body
                
            div = etree.SubElement(self.context_node, "div")

            if content.be_type == "wom":
                div.set("type", "biography")
                div.set("subtype", "woman")
            elif content.be_type == "man":
                div.set("type", "biography")
                div.set("subtype", "man")
            elif content.be_type == "rep":
                div.set("type", "biography")
                div.set("subtype", "ref_or_rep")
            elif content.be_type == "names":
                div.set("type", "names")
            elif content.be_type == "event":
                div.set("type", "event")
            elif content.be_type == "events":
                div.set("type", "events")
        
            self.context_node = div
        # elif isinstance(content, DictionaryUnit):
        #     entry_free = teiDoc.createElementNS(TEINS, "entryFree")
        #     if content.dic_type == "bib":
        #         entry_free.setAttribute("type", "bib")
        #     elif content.dic_type == "lex":
        #         entry_free.setAttribute("type", "lex")
        #     elif content.dic_type == "nis":
        #         entry_free.setAttribute("type", "nis")
        #     elif content.dic_type == "top":
        #         entry_free.setAttribute("type", "top")
        #     entry_free.appendChild(teiDoc.createTextNode(content.value))
        #     parent.appendChild(entry_free)
        # elif isinstance(content, DoxographicalItem):
        #     doxo_div = teiDoc.createElementNS(TEINS, "div")
        #     doxo_div.setAttribute("type", "doxographical")
        #     if content.dox_type == "pos":
        #         doxo_div.setAttribute("subtype", "pos")
        #     elif content.dox_type == "sec":
        #         doxo_div.setAttribute("subtype", "sec")
        #     doxo_div.appendChild(teiDoc.createTextNode(content.value))
        #     parent.appendChild(doxo_div)
        # elif isinstance(content, Editorial):
        #     ed_div = teiDoc.createElementNS(TEINS, "div")
        #     ed_div.setAttribute("type", "editorial")
        #     ## TODO: THE FOLLOWING CONTENT MUST BE CONTAINED. BUT WHEN DOES IT STOP?
        #     parent.appendChild(ed_div)
