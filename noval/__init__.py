import threading
import gettext
from noval import ui_lang


_lock = threading.Lock()

def NewId():
    global _idCounter
    
    with _lock:
        _idCounter += 1
    return _idCounter

def GetApp():
    global _AppInstance
    
    assert(_AppInstance is not None)
    return _AppInstance

class Locale(object):
    
    LANGUAGE_NAMES = {
        ui_lang.LANGUAGE_CHINESE_SIMPLIFIED:'zh_CN',
        ui_lang.LANGUAGE_ENGLISH_US:'en_US'
    }
    
    def __init__(self,lang_id):
        self._lang_id = lang_id
        self._domains = []
        self._trans = []
        self._lookup_dirs = []

    def AddCatalogLookupPathPrefix(self,lookup_dir):
        if lookup_dir not in self._lookup_dirs:
            self._lookup_dirs.append(lookup_dir)
    
    def AddCatalog(self,domain):
        
        if domain in self._domains:
            raise RuntimeError("domain %s already exist in locale domains" % domain)
        self._domains.append(domain)
        
        for lookup_dir in self._lookup_dirs:
            t = gettext.translation(domain, lookup_dir, languages = [self.GetLanguageName()],fallback=True)
            self._trans.append(t)
            
    def GetLanguageName(self):
        return Locale.LANGUAGE_NAMES[self._lang_id]
        
    def GetText(self,raw_text):
        for tran in self._trans:
            to_text = tran.gettext(raw_text)
            if to_text != raw_text:
                return to_text
        return raw_text
        
    @classmethod
    def IsAvailable(cls,lang_id):
        return lang_id in cls.LANGUAGE_NAMES
        
def GetTranslation(raw_text):
    global _AppInstance
    assert (_AppInstance is not None)
    return _AppInstance.GetLocale().GetText(raw_text)
    
_ = GetTranslation

_idCounter = 1000
_AppInstance = None

