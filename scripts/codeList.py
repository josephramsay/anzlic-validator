import lxml
from urllib import request
from lxml import etree

NSX = {'gml'    :   'http://www.opengis.net/gml/3.2',
       'xsi'    :   'http://www.w3.org/2001/XMLSchema-instance',
       'cat'    :   'http://standards.iso.org/iso/19115/-3/cat/1.0',
       'lan'    :   'http://standards.iso.org/iso/19115/-3/lan/1.0',
       'gco'    :   'http://standards.iso.org/iso/19115/-3/gco/1.0',
       'xlink'  :   'http://www.w3.org/1999/xlink'}

url = "http://standards.iso.org/iso/19115/resources/Codelist/cat/codelists.xml"
codeListURL = request.urlopen(url)
cdl = etree.parse(codeListURL)
root = cdl.getroot()


SELSS = ('MD_ProgressCode', 'MD_MaintenanceFrequencyCode', 'MD_SpatialRepresentationCode',)
SELSM = ('MD_TopicCategoryCode',)
SELMS = ('CI_DateTypeCode',)

def finder(root):
    codelist = ()
    for el in root.findall('cat:codeEntry/cat:CT_CodelistValue/cat:identifier/gco:ScopedName', namespaces=NSX):
        codelist +=  (el.text[len(root.attrib['id'])+1:],)
    return codelist

def codeList(name):
    for el in root.findall('cat:codelistItem/cat:CT_Codelist', namespaces=NSX):
        if str(el.attrib['id']) == name:
               return finder(el)

