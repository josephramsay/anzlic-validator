import re
import os
import base64

KEYINDEX = 0

class Authentication(object):
    '''Static methods to read keys/user/pass from files'''
    
    @staticmethod
    def userpass(upfile):
        return (Authentication.searchfile(upfile,'username'),Authentication.searchfile(upfile,'password'))
        
    @staticmethod
    def apikey(keyfile,kk='key',keyindex=None):
        '''Returns current key from a keyfile advancing KEYINDEX on subsequent calls (if ki not provided)'''
        global KEYINDEX
        key = Authentication.searchfile(keyfile,'{0}{1}'.format(kk,keyindex or KEYINDEX))
        if not key and not keyindex:
            KEYINDEX = 0
            key = Authentication.searchfile(keyfile,'{0}{1}'.format(kk,KEYINDEX))
        elif not keyindex:
            KEYINDEX += 1
        return key
    
    @staticmethod
    def creds(cfile):
        '''Read CIFS credentials file'''
        return (Authentication.searchfile(cfile,'username'),\
                Authentication.searchfile(cfile,'password'),\
                Authentication.searchfile(cfile, 'domain'))
    
    @staticmethod
    def searchfile(spf,skey,default=None):
        #value = default
        #look in current then app then home
        sp,sf = os.path.split(spf)
        spath = (sp,'',os.path.expanduser('~'),os.path.dirname(__file__))
        first = [os.path.join(p,sf) for p in spath if os.path.lexists(os.path.join(p,sf))][0]
        with open(first,'r') as h:
            for line in h.readlines():
                k = re.search('^{key}=(.*)$'.format(key=skey),line)
                if k: return k.group(1)
        return default
    
    @staticmethod
    def getHeader(korb,kfile):
        '''Convenience method for auth header'''
        if korb.lower() == 'basic':
            b64s = base64.encodestring('{0}:{1}'.format(*Authentication.userpass(kfile))).replace('\n', '')
            return ('Authorization', 'Basic {0}'.format(b64s))
        elif korb.lower() == 'key':
            key = Authentication.apikey(kfile)
            return ('Authorization', 'key {0}'.format(key))
        return None # Throw something
    
