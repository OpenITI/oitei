TEI_TEMPLATE = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
 <teiHeader>
     <fileDesc>
        <titleStmt>
           <title></title>
        </titleStmt>
        <publicationStmt>
           <p/>
        </publicationStmt>
        <sourceDesc>
           <p/>
        </sourceDesc>
     </fileDesc>
     <profileDesc>
      <calendarDesc>
         <calendar xml:id="ah">
            <p>Anno Hegirae</p>
         </calendar>
      </calendarDesc>
     </profileDesc>
 </teiHeader>
 <text>
    <body/>
 </text>
</TEI>"""

DECLS = """<?xml version='1.0' encoding='UTF-8'?>
<?xml-model href="https://raw.githubusercontent.com/OpenITI/tei_openiti/master/tei_openiti.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="https://raw.githubusercontent.com/OpenITI/tei_openiti/master/tei_openiti.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>
"""