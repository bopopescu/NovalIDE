#-----------------------------------------------------------------------------#
import os
from noval.tool.consts import _

#-----------------------------------------------------------------------------#

def _NewId():
    global _idCounter
    _idCounter += 1
    return _idCounter

_idCounter = 32100

#-----------------------------------------------------------------------------#

#---- Language Identifiers Keys ----#
# Used for specifying what dialect/keyword set to load for a specific lexer

#---- Use LEX_NULL ----#
ID_LANG_TXT  = _NewId()
LANG_TXT = _('Text File')

ID_LANG_C = _NewId()
LANG_C = _('C Source File')


ID_LANG_CPP = _NewId()
LANG_CPP = _('C++ Source File')

ID_LANG_H = _NewId()
LANG_H = _('C/C++ Header File')

# Use LEX_CSS
ID_LANG_CSS = _NewId()
LANG_CSS = _('StyleSheet File')

ID_LANG_HTML = _NewId()
LANG_HTML = _('HTML File')

ID_LANG_JS   = _NewId()
LANG_JS = _('JavaScript File')

ID_LANG_XML  = _NewId()
LANG_XML = _('XML File')
ID_LANG_SGML  = _NewId()

ID_LANG_PYTHON = _NewId()
LANG_PYTHON = _('Python Script')

ID_LANG_PROPS = _NewId()
LANG_PROPS = _('Properties File')

# Use LEX_YAML
ID_LANG_YAML = _NewId()
LANG_YAML = _('YAML File')

ID_LANG_BASH   = _NewId()
LANG_BASH = _('Bash Shell Script')

ID_LANG_SQL = _NewId()
LANG_SQL = _('SQL Script')

ID_LANG_PERL = _NewId()
LANG_PERL = _('Perl Script')

# Maps file types to syntax definitions
LANG_MAP = {
            ID_LANG_BASH   : (LANG_BASH,   'bsh sh configure'),
       ##     LANG_BATCH  : (ID_LANG_BATCH,     '_batch'),
            ID_LANG_C      : (LANG_C,      'c'),
            ID_LANG_CPP    : (LANG_CPP,    'cc c++ cpp cxx hh h++ hpp hxx'),
            ID_LANG_H      : (LANG_H,      'h'),
            ID_LANG_CSS    : (LANG_CSS,    'css'),
            ID_LANG_JS     : (LANG_JS,     'js'),
            ID_LANG_HTML   : (LANG_HTML,   'htm html shtm shtml xhtml'),
            ID_LANG_PROPS  : (LANG_PROPS,  'ini inf reg url cfg cnf'),
            ID_LANG_PYTHON : (LANG_PYTHON, 'py pyw'),
            ID_LANG_SQL    : (LANG_SQL,    'sql'),
            ID_LANG_TXT    : (LANG_TXT,    'txt text'),
            ID_LANG_XML    : (LANG_XML,    'axl dtd plist rdf svg xml xrc xsd xsl xslt xul'),
            ID_LANG_YAML   : (LANG_YAML,   'yaml yml'),
            ID_LANG_PERL   : (LANG_PERL,   'pl')
}


### TODO: Profiling on the following methods to see if caching is necessary ###

# Dynamically finds the language description string that matches the given
# language id.
# Used when manually setting lexer from a menu/dialog
def GetDescriptionFromId(lang_id):
    """Get the programming languages description string from the given
    language id. If no corresponding language is found the plain text
    description is returned.
    @param lang_id: Language Identifier ID
    @note: requires that all languages are defined in ID_LANG_NAME, LANG_NAME
           pairs to work properly.

    """
    rval = LANG_TXT
    # Guard against async code that may be modifying globals
    globs = dict(globals())
    for key, val in globs.iteritems():
        if val == lang_id and key.startswith('ID_LANG'):
            rval = globs.get(key[3:], LANG_TXT)
            break
    return rval

def GetIdFromDescription(desc):
    """Get the language identifier for the given file type string. The search
    is case insensitive.
    @param desc: unicode (i.e u"Python")
    @note: if lookup fails ID_LANG_TXT is returned

    """
    rval = ID_LANG_TXT
    desc = desc.lower()
    # Guard against async code that may be modifying globals
    globs = dict(globals())
    for key, val in globs.iteritems():
        if isinstance(val, unicode):
            if val.lower() == desc and key.startswith('LANG_'):
                rval = globs.get("ID_" + key, ID_LANG_TXT)
                break
    return rval
    
def RegisterNewLangId(langId, langName):
    """Register a new language identifier
    @param langId: "ID_LANG_FOO"
    @param langName: "Foo"
    @return: int

    """
    gdict = globals()
    if langId not in gdict:
        gdict[langId] = _NewId()
        gdict[langId[3:]] = langName
    return gdict[langId]

    
