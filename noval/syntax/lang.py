
def NewLangId():
    global _idCounter
    _idCounter += 1
    return _idCounter

_idCounter = 32100



ID_LANG_TXT  = NewLangId()


def RegisterNewLangId(langId):
    """Register a new language identifier
    @param langId: "ID_LANG_FOO"
    @return: int

    """
    gdict = globals()
    if langId not in gdict:
        gdict[langId] = NewLangId()
    return gdict[langId]