import oimdp
from oimdp.structures import AdministrativeRegion, BioOrEvent, Content, DictionaryUnit, DoxographicalItem, Editorial, Hemistich, Hukm, Isnad, Line, LinePart, Matn, PageNumber, Paragraph, Riwayat, SectionHeader, TextPart, Verse
from lxml import etree
from lxml.etree import Element

from oitei.tei_template import TEI_TEMPLATE

TEINS = "{http://www.tei-c.org/ns/1.0}"

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
        self.context_linepart = None
        
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

        if self.doc is not None:
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
            self._convertStructure(content)
        

    def _convertStructure(self, content):
        """Convert an oimdp.Content object to a TEI element"""

        PARALIKE = [f"{TEINS}p", f"{TEINS}ab"]
        DIVLIKE = [f"{TEINS}div", f"{TEINS}entryFree"]

        def _set_closest_container():
            """ set the context node to closest div or body """
            if self.context_node.tag != f"{TEINS}body":
                # Locate closest div
                closest = self.context_node.xpath("ancestor::tei:div[not(@type)]", namespaces=NS)

                if len(closest):
                    self.context_node = closest[0]
                else:
                    # Return to body
                    self.context_node = self.body

        def _create_p(tag="p", attributes={}):
            if self.context_node.tag not in DIVLIKE:
                # Locate closest div like structure
                closest = self.context_node.xpath("ancestor::tei:div", namespaces=NS)

                if len(closest):
                    self.context_node = closest[0]
                else:
                    # If there is no div, create one.
                    div = etree.SubElement(self.body, f"{TEINS}div")
                    if attributes:
                        for att in attributes:
                            div.set(att, attributes[att])
                    self.context_node = div
            
            self.context_node = etree.SubElement(self.context_node, f"{TEINS}{tag}")

        # LINE PARTS 
        if isinstance(content, Isnad) or isinstance(content, Matn) or isinstance(content, Hukm):
            parts = {
                "Isnad": "isn",
                "Matn": "matn",
                "Hukm": "hukm",
            }

            if self.context_node.tag != f"{TEINS}ab":
                raise Exception("Riwāyāt part not in Riwāyāt")
            
            seg = etree.SubElement(self.context_node, f"{TEINS}seg")
            part_type = parts.get(type(content).__name__)
            seg.set("type", part_type)
            
            self.context_linepart = seg

        elif isinstance(content, Hemistich):
            if self.context_node.tag != f"{TEINS}l":
                raise Exception("Hemistic outside of Verse structure")
            else:
                # TODO: THIS MUST BE UPDATED IN THE SCHEMA: Use caesura instead of seg type hemi
                c = etree.SubElement(self.context_node, f"{TEINS}caesura")
                c.tail = " "

        elif isinstance(content, TextPart):
            node = self.context_node
            if self.context_linepart is not None:
                node = self.context_linepart
            self._appendText(node, content.orig.strip())

        else:
            self.context_linepart = None


        # Riwāyāt -- NEEDS correction in TEI customization: <p> does not have a type. Use <ab>.
        if isinstance(content, Riwayat):
            _create_p(tag="ab", attributes={"type": "rwy"})

        elif isinstance(content, Paragraph):
            _create_p()

        elif isinstance(content, PageNumber):
            pb = etree.SubElement(self.context_node, f"{TEINS}pb")
            value = ""
            if int(content.volume) > 0:
                value += f"Vol. {int(content.volume)}, "
            if int(content.page) > 0:
                value += f"p. {int(content.page)}"
                pb.set("n", value)

        elif isinstance(content, Verse):
            if self.context_node.tag != f"{TEINS}lg":
                _set_closest_container()
                self.context_node = etree.SubElement(self.context_node, f"{TEINS}lg")
            
            self.context_node = etree.SubElement(self.context_node, f"{TEINS}l")

            if len(content.parts) > 0:
                for part in content.parts:
                    self._convertStructure(part)
                self._appendText(self.context_node, "\n")
            self.context_node = self.context_node.getparent()

        elif isinstance(content, Line):
            if self.context_node.tag not in PARALIKE:
                _create_p()

            etree.SubElement(self.context_node, f"{TEINS}lb")

            if len(content.parts) > 0:
                for part in content.parts:
                    self._convertStructure(part)
                self._appendText(self.context_node, "\n")

        elif isinstance(content, SectionHeader):
            # make sure we are in a section (untyped) div ...
            if self.context_node.tag != f"{TEINS}div" or self.context_node.get("type"):
                # ... or find the closest ...
                closest = self.context_node.xpath("ancestor::tei:div[not(@type)] | ancestor::tei:body", namespaces=NS)
                if len(closest):
                    self.context_node = closest[-1]
                else:
                    # ... or create it.
                    self.context_node = etree.SubElement(self.context_node, f"{TEINS}div")
            
            # Check level
            cur_level = len(self.context_node.xpath("ancestor-or-self::tei:div[not(@type)]", namespaces=NS))
            level_diff = content.level - cur_level

            if level_diff >= 0:
                # Needs nesting or is at the coorect level (level_diff == 0 and the loop is noop).
                for step in range(level_diff):
                    self.context_node = etree.SubElement(self.context_node, f"{TEINS}div")
            else:
                # Needs to step out by the level difference.
                ancestor = self.context_node.xpath("ancestor::tei:div[not(@type)]", namespaces=NS)[level_diff]
                if ancestor:
                    self.context_node = ancestor
                else:
                    raise Exception("Could not parse nesting of sections based on headers.")

            head = etree.SubElement(self.context_node, f"{TEINS}head")
            head.text = content.value.strip()

            # Create new div
            # div = etree.SubElement(self.context_node, "div")

        # elif isinstance(content, AdministrativeRegion):
            #TODO IN PARSER!
            
        elif isinstance(content, BioOrEvent):
            _set_closest_container()
                
            div = etree.SubElement(self.context_node, f"{TEINS}div")

            if content.be_type == "wom":
                div.set("type", "biography")
                div.set("subtype", "woman")
            elif content.be_type == "man":
                div.set("type", "biography")
                div.set("subtype", "man")
            elif content.be_type == "ref":
                div.set("type", "biography")
                div.set("subtype", "ref_or_rep")
            elif content.be_type == "names":
                div.set("type", "names")
            elif content.be_type == "event":
                div.set("type", "event")
            elif content.be_type == "events":
                div.set("type", "events")
        
            self.context_node = div

        elif isinstance(content, DictionaryUnit):
            _set_closest_container()
                
            ef = etree.SubElement(self.context_node, f"{TEINS}entryFree")

            if content.dic_type == "bib":
                ef.set("type", "bib")
            elif content.dic_type == "lex":
                ef.set("type", "lex")
            elif content.dic_type == "nis":
                ef.set("type", "nis")
            elif content.dic_type == "top":
                ef.set("type", "top")
        
            self.context_node = ef
        elif isinstance(content, DoxographicalItem):
            _set_closest_container()

            div = etree.SubElement(self.context_node, f"{TEINS}div")
            div.set("type", "doxographical")

            if content.dox_type == "pos":
                div.set("subtype", "pos")
            elif content.dox_type == "sec":
                div.set("subtype", "sec")

            self.context_node = div
        elif isinstance(content, Editorial):
            _set_closest_container()

            div = etree.SubElement(self.context_node, f"{TEINS}div")
            div.set("type", "editorial")

            self.context_node = div

        # Morphological Patterns
