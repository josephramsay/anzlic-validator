from lxml import etree
from abc import ABCMeta, abstractmethod
import os
import urllib2


class SCHMD(object):
    
    __metaclass__ = ABCMeta
    
    sch = None
    md = None
    
    def __init__(self):
        self.schema()
        #self.metadata()
        
    @abstractmethod
    def schema(self):
        '''schema init'''    
        
    @abstractmethod
    def metadata(self):
        '''schema init'''
        
class Local(SCHMD):
    
    SP = '../../ANZLIC-XML/standards.iso.org/iso/19110/gfc/1.1/'
    TP = '../tests/data/'
    
    def __init__(self):
        super(Local,self).__init__()
    
    def schema(self):
        sch_name = 'featureCatalogue.xsd'#metadataEntity?
        sch_path = os.path.abspath(os.path.join(os.path.dirname(__file__),self.SP,sch_name))
        
        sch_doc = etree.parse(sch_path)
        self.sch = etree.XMLSchema(sch_doc)
        
    def metadata(self):
        md_name = 'nz-primary-parcels.iso.xml'    
        md_path = os.path.abspath(os.path.join(os.path.dirname(__file__),self.TP,md_name))
        self.md = etree.parse(md_path)

class Remote(SCHMD):  
    
    def __init__(self):
        super(Remote,self).__init__()  
    
    def schema(self):
        sch_name = 'http://www.isotc211.org/2005/gmd/metadataEntity.xsd'
        sch_handle = urllib2.urlopen(sch_name)
        
        sch_doc = etree.parse(sch_handle)
        self.sch = etree.XMLSchema(sch_doc)    
        
    def metadata(self,lid):
        md_name = 'https://data.linz.govt.nz/layer/{lid}-nz-primary-parcels/metadata/iso/xml/'    
        md_handle = urllib2.urlopen(md_name.format(lid=lid))
        
        self.md = etree.parse(md_handle)
        
        
def conditionalTest(md):
    
    GMD = '{http://www.isotc211.org/2005/gmd}'
    GCO = '{http://www.isotc211.org/2005/gco}'
    DATASET = False
        
    tree = md
    root = tree.getroot()
        
    for element in root.find(GMD+'hierarchyLevel'):
        if element.get('codeListValue') == None:
            # 'ERROR: No Hierarchy Level Declared'
            return False
        elif element.get('codeListValue') == 'dataset':
            DATASET = True  
    
    if DATASET:
        IDIN = root.find(GMD+'identificationInfo')
        for MDDID in IDIN.iter(GMD+'MD_DataIdentification'):
            if MDDID.find(GMD+'topicCategory/'+GMD+'MD_TopicCategoryCode') is None:
                # 'ERROR: No Topic Category Declared'
                return False
            if MDDID.find(GMD+'extent') is None:
                # 'ERROR: No Extent Declared'
                return False
            else:
                EX = MDDID.find(GMD+'extent/'+GMD+'EX_Extent/'+GMD+'geographicElement')
                if EX.find(GMD+'EX_GeographicBoundingBox') is None and EX.find(GMD+'EX_GeographicDescription') is None:
                    #'ERROR: No Geographic Bounding Box or Geographic Description Declared'
                    return False

    if root.find(GMD+'language/'+GCO+'CharacterString') is None:
       return False
   
    if root.find(GMD+'characterSet/'+GMD+'MD_CharacterSetCode') is None:
       return False
   
    MDDID = root.find(GMD+'identificationInfo/'+GMD+'MD_DataIdentification')
    if MDDID.find(GMD+'language/'+GCO+'CharacterString') is None:
       return False
   
    if MDDID.find(GMD+'characterSet/'+GMD+'MD_CharacterSetCode') is None:
       return False
    
    return True


def main():
    
    #v1 = Local()
    #print(v1.sch.validate(v1.md))
    succeed = ('50772',)
    fail = ('50813','51362','51920', '51939', '50157')
    
    v2 = Remote()
    for lid in succeed+fail:
        v2.metadata(lid)    
        if v2.sch.validate(v2.md):
            print (lid, conditionalTest(v2.md))
        else:
            print (lid, False)


        
    
if __name__ == "__main__":
    main()