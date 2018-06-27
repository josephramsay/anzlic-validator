import lxml
import urllib2
from lxml import etree

NSX = {'gml'    :   'http://www.opengis.net/gml/3.2',
       'xsi'    :   'http://www.w3.org/2001/XMLSchema-instance',
       'cat'    :   'http://standards.iso.org/iso/19115/-3/cat/1.0',
       'lan'    :   'http://standards.iso.org/iso/19115/-3/lan/1.0',
       'gco'    :   'http://standards.iso.org/iso/19115/-3/gco/1.0',
       'xlink'  :   'http://www.w3.org/1999/xlink',
       'gmx'    :   'http://www.isotc211.org/2005/gmx'}

url = "http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml"
codeListURL = urllib2.urlopen(url)
cdl = etree.parse(codeListURL)
root = cdl.getroot()


def finder(root):
    codelist = ()
    for el in root.findall('gmx:codeEntry/gmx:CodeDefinition/gml:identifier', namespaces=NSX):
        codelist += (el.text,)
    return codelist


def codeList(name):
    for el in root.findall('gmx:codelistItem/gmx:CodeListDictionary', namespaces=NSX):
        if el.xpath('@gml:id', namespaces=NSX)[0] == name:
            return finder(el)


