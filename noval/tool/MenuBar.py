import wx
from noval.tool.consts import _,VIEW_MENU_ORIG_NAME,HELP_MENU_ORIG_NAME,WINDOWS_MENU_ORIG_NAME
from noval.util.exceptions import MenuBarMenuNotExistError

class KeyBinder(object):
    """Class for managing keybinding configurations"""
    cprofile = None # Current Profile Name String
    keyprofile = dict() # Active Profile (dict)

    def __init__(self):
        """Create the KeyBinder object"""
        super(KeyBinder, self).__init__()

        # Attributes
        self.cache = ed_glob.CONFIG['CACHE_DIR'] # Resource Directory

    def GetBinding(self, item_id):
        """Get the keybinding string for use in a menu
        @param item_id: Menu Item Id
        @return: string

        """
        rbind = self.GetRawBinding(item_id)
        shortcut = u''
        if rbind is not None:
            shortcut = u"+".join(rbind)
            if len(shortcut):
                shortcut = u"\t" + shortcut
        return unicode(shortcut)

    @classmethod
    def GetCurrentProfile(cls):
        """Get the name of the currently set key profile if one exists
        @param cls: Class Object
        @return: string or None

        """
        return cls.cprofile

    @classmethod
    def GetCurrentProfileDict(cls):
        """Get the dictionary of keybindings
        @param cls: Class Object
        @return: dict

        """
        return cls.keyprofile

    @staticmethod
    def GetKeyProfiles():
        """Get the list of available key profiles
        @return: list of strings

        """
        recs = util.GetResourceFiles(u'cache', trim=True, get_all=False,
                                     suffix='.ekeys', title=False)
        if recs == -1:
            recs = list()

        tmp = util.GetResourceFiles(u'ekeys', True, True, '.ekeys', False)
        if tmp != -1:
            recs.extend(tmp)

        return recs

    def GetProfilePath(self, pname):
        """Get the full path to the given keyprofile
        @param pname: profile name
        @return: string or None
        @note: expects unique name for each profile in the case that
               a name exists in both the user and system paths the one
               found on the user path will be returned.

        """
        if pname is None:
            return None

        rname = None
        for rec in self.GetKeyProfiles():
            if rec.lower() == pname.lower():
                rname = rec
                break

        # Must be a new profile
        if rname is None:
            rname = pname

        kprof = u"%s%s.ekeys" % (ed_glob.CONFIG['CACHE_DIR'], rname)
        if not os.path.exists(kprof):
            # Must be a system supplied keyprofile
            rname = u"%s%s.ekeys" % (ed_glob.CONFIG['KEYPROF_DIR'], rname)
            if not os.path.exists(rname):
                # Doesn't exist at syspath either so instead assume it is a new
                # custom user defined key profile.
                rname = kprof
        else:
            rname = kprof

        return rname

    @classmethod
    def GetRawBinding(cls, item_id):
        """Get the raw key binding tuple
        @param cls: Class Object
        @param item_id: MenuItem Id
        @return: tuple

        """
        return cls.keyprofile.get(item_id, None)

    @classmethod
    def FindMenuId(cls, keyb):
        """Find the menu item ID that the
        keybinding is currently associated with.
        @param cls: Class Object
        @param keyb: tuple of unicode (u'Ctrl', u'C')
        @return: int (-1 if not found)

        """
        menu_id = -1
        for key, val in cls.keyprofile.iteritems():
            if val == keyb:
                menu_id = key
                break
        return menu_id

    @classmethod
    def LoadDefaults(cls):
        """Load the default key profile"""
        cls.keyprofile = dict(_DEFAULT_BINDING)
        cls.cprofile = None

    def LoadKeyProfile(self, pname):
        """Load a key profile from profile directory into the binder
        by name.
        @param pname: name of key profile to load

        """
        if pname is None:
            ppath = None
        else:
            ppath = self.GetProfilePath(pname)
        self.LoadKeyProfileFile(ppath)

    def LoadKeyProfileFile(self, path):
        """Load a key profile from the given path
        @param path: full path to file

        """
        keydict = dict()
        pname = None
        if path:
            pname = os.path.basename(path)
            pname = pname.rsplit('.', 1)[0]

        if pname is not None and os.path.exists(path):
            reader = util.GetFileReader(path)
            if reader != -1:
                util.Log("[keybinder][info] Loading KeyProfile: %s" % path)
                for line in reader:
                    parts = line.split(u'=', 1)
                    # Check that the line was formatted properly
                    if len(parts) == 2:
                        # Try to find the ID value
                        item_id = _GetValueFromStr(parts[0])
                        if item_id is not None:
                            tmp = [ part.strip()
                                    for part in parts[1].split(u'+')
                                    if len(part.strip()) ]

                            # Do some checking if the binding is valid
                            nctrl = len([key for key in tmp
                                         if key not in (u'Ctrl', u'Alt', u'Shift')])
                            if nctrl:
                                if parts[1].strip().endswith(u'++'):
                                    tmp.append(u'+')
                                kb = tuple(tmp)
                                if kb in keydict.values():
                                    for mid, b in keydict.iteritems():
                                        if kb == b:
                                            del keydict[mid]
                                            break
                                keydict[item_id] = tuple(tmp)
                            else:
                                # Invalid key binding
                                continue

                reader.close()
                KeyBinder.keyprofile = keydict
                KeyBinder.cprofile = pname
                return
            else:
                util.Log("[keybinder][err] Couldn't read %s" % path)
        elif pname is not None:
            # Fallback to default keybindings
            util.Log("[keybinder][err] Failed to load bindings from %s" % pname)

        util.Log("[keybinder][info] Loading Default Keybindings")
        KeyBinder.LoadDefaults()

    def SaveKeyProfile(self):
        """Save the current key profile to disk"""
        if KeyBinder.cprofile is None:
            util.Log("[keybinder][warn] No keyprofile is set, cant save")
        else:
            ppath = self.GetProfilePath(KeyBinder.cprofile)
            writer = util.GetFileWriter(ppath)
            if writer != -1:
                itemlst = list()
                for item in KeyBinder.keyprofile.keys():
                    itemlst.append(u"%s=%s%s" % (_FindStringRep(item),
                                                self.GetBinding(item).lstrip(),
                                                os.linesep))
                writer.writelines(sorted(itemlst))
                writer.close()
            else:
                util.Log("[keybinder][err] Failed to open %s for writing" % ppath)

    @classmethod
    def SetBinding(cls, item_id, keys):
        """Set the keybinding of a menu id
        @param cls: Class Object
        @param item_id: item to set
        @param keys: string or list of key strings ['Ctrl', 'S']

        """
        if isinstance(keys, basestring):
            keys = [ key.strip() for key in keys.split(u'+')
                     if len(key.strip())]
            keys = tuple(keys)

        if len(keys):
            # Check for an existing binding
            menu_id = cls.FindMenuId(keys)
            if menu_id != -1:
                del cls.keyprofile[menu_id]
            # Set the binding
            cls.keyprofile[item_id] = keys
        elif item_id in cls.keyprofile:
            # Clear the binding
            del cls.keyprofile[item_id]
        else:
            pass

    @classmethod
    def SetProfileName(cls, pname):
        """Set the name of the current profile
        @param cls: Class Object
        @param pname: name to set profile to

        """
        cls.cprofile = pname

    @classmethod
    def SetProfileDict(cls, keyprofile):
        """Set the keyprofile using a dictionary of id => bindings
        @param cls: Class Object
        @param keyprofile: { menu_id : (u'Ctrl', u'C'), }

        """
        cls.keyprofile = keyprofile
        
class MainMenuBar(wx.MenuBar):
    """Custom menubar to allow for easier access and updating
    of menu components.
    @todo: redo all of this

    """
    ###keybinder = KeyBinder()

    def __init__(self, style=0):
        
        super(MainMenuBar, self).__init__(style)

    def GetMenuByName(self,menu_name):
        menu_index = self.FindMenu(menu_name)
        if 0 > menu_index:
            raise MenuBarMenuNotExistError(menu_name)
        return self.GetMenu(menu_index)

    def GetFileMenu(self):
        pass
        
    def GetEditMenu(self):
        pass
        
    def GetViewMenu(self):
        return self.GetMenuByName(_(VIEW_MENU_ORIG_NAME))
        
    def GetFomatMenu(self):
        pass
        
    def GetProjectMenu(self):
        pass
        
    def GetRunMenu(self):
        pass
        
    def GetToolsMenu(self):
        pass
        
    def GetWindowsMenu(self):
        return self.GetMenuByName(_(WINDOWS_MENU_ORIG_NAME))

    def GetHelpMenu(self):
        return self.GetMenuByName(_(HELP_MENU_ORIG_NAME))
