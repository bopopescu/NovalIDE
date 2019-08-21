# -*- coding: utf-8 -*-
import noval.syntax.syntax as syntax
import zlib
import noval.util.compat as compat
import noval.util.utils as utils
import time

class BaseLexer(object):
    """Syntax data container object base class"""
    
    SYNTAX_ITEMS = []
    def __init__(self, langid):
        object.__init__(self)
        # Attributes
        self._langid = langid
        self.exts = []
        self.style_items = []

    @property
    def CommentPattern(self):
        return self.GetCommentPattern()

    @property
    def Keywords(self):
        return self.GetKeywords()

    @property
    def LangId(self):
        return self.GetLangId()

    #---- Interface Methods ----#

    def GetCommentPattern(self):
        """Get the comment pattern
        @return: list of strings ['/*', '*/']

        """
        return list()

    def GetKeywords(self):
        """Get the Keyword List(s)
        @return: list of tuples [(1, ['kw1', kw2']),]

        """
        return list()

    def GetLangId(self):
        """Get the language id
        @return: int

        """
        return self._langid

    def SetLangId(self, lid):
        """Set the language identifier
        @param lid: int

        """
        self._langid = lid
        
    def Register(self):
        syntax.SyntaxThemeManager().Register(self)

    def UnRegister(self):
        syntax.SyntaxThemeManager().UnRegister(self)
        
    def GetDescription(self):
        return ""
        
    def GetShowName(self):
        return ""
        
    def GetDefaultExt(self):
        return ""
        
    def GetExt(self):
        return ""
        
    def GetDocTypeName(self):
        return ""
        
    def GetViewTypeName(self):
        return ""
        
    def GetDocTypeClass(self):
        return None
        
    def GetViewTypeClass(self):
        return None
        
    def GetDocIcon(self):
        return None
        
    def GetSampleCode(self):
        return ''
        
    def GetCommentTemplate(self):
        return None
        
    def IsCommentTemplateEnable(self):
        return self.GetCommentTemplate() is not None
        
    @property
    def StyleItems(self):
        return self.style_items
        
    def GetExtStr(self):
        if len(self.Exts) == 0:
            return ""
        strext = "*." + self.Exts[0]
        for ext in self.Exts[1:]:
            strext += ";"
            strext += "*."
            strext +=  ext
        return strext
        
    def ContainExt(self,ext):
        ext = ext.replace(".","")
        for ext_name in self.Exts:
            if ext.lower() == ext_name:
                return True
        return False
            
    def GetSampleCodeFromFile(self,sample_file_path,is_zip_compress = True):
        if not is_zip_compress:
            with open(sample_file_path) as f:
                return f.read()
        else:
            content = ''
            with open(sample_file_path, 'rb') as f:
                decompress = zlib.decompressobj()
                data = f.read(1024)
                while data:
                    if utils.is_py2():
                        content += decompress.decompress(data)
                    else:
                        content += compat.ensure_string(decompress.decompress(data))
                    data = f.read(1024)
                if utils.is_py2():
                    content += decompress.flush()
                else:
                    content += compat.ensure_string(decompress.flush())
            return content
        
    def IsVisible(self):
        return True
        
    @property
    def Exts(self):
        if 0 == len(self.exts):
            self.exts = self.GetExt().split()
        return self.exts


class BaseSyntaxcolorer:

    BASE_TAGDEFS = {
            "TODO",
            "SYNC",
        }
    def __init__(self,text):
        self.text = text
        self.after_id = None
        self.allow_colorizing = True
        self.colorizing = False
        self.stop_colorizing = False
        self._use_coloring = False
        self.tagdefs = {
            "comment",
            "string",
            "keyword",
            "number",
            "builtin"
        }
        self.tagdefs.update(BaseSyntaxcolorer.BASE_TAGDEFS)

    def schedule_update(self, event, use_coloring=True):
        self.allow_colorizing = use_coloring
        # Allow reducing work by remembering only changed lines
        #插入删除文本
        if hasattr(event, "sequence"):
            if event.sequence == "TextInsert":
                start_index = event.index
                end_index = start_index + "+%dc" % len(event.text)
            elif event.sequence == "TextDelete":
                start_index = event.index1
                end_index = event.index2
        else:
            #高亮语法设置更改
            start_index = "1.0"
            end_index = "end"

        self.notify_range(start_index,end_index)

    def notify_range(self, index1, index2=None):
        self.text.tag_add("TODO", index1, index2)
        if self.after_id:
            utils.get_logger().debug("colorizing already scheduled")
            return
        if self.colorizing:
            self.stop_colorizing = True
            utils.get_logger().debug("stop colorizing")
        if self.allow_colorizing:
            utils.get_logger().debug("schedule colorizing")
            self.after_id = self.text.after(1, self.recolorize)
        #不高亮语法,删除所有tag
        else:
            self.RemoveTags(index1,index2)

    def recolorize(self):
        self.after_id = None
        if not self.allow_colorizing:
            utils.get_logger().debug("auto colorizing is off")
            return
        if self.colorizing:
            utils.get_logger().debug("already colorizing")
            return
        try:
            self.stop_colorizing = False
            self.colorizing = True
            utils.get_logger().debug("colorizing...")
            self._update_coloring()
        finally:
            self.colorizing = False
        if self.allow_colorizing and self.text.tag_nextrange("TODO", "1.0"):
            utils.get_logger().debug("reschedule colorizing")
            self.after_id = self.text.after(1, self.recolorize)

    @utils.compute_run_time
    def _update_coloring(self):
        next = "1.0"
        while True:
            item = self.text.tag_nextrange("TODO", next)
            if not item:
                break
            head, tail = item
            self.text.tag_remove("SYNC", head, tail)
            item = self.text.tag_prevrange("SYNC", head)
            if item:
                head = item[1]
            else:
                head = "1.0"

            chars = ""
            next = head
            lines_to_get = 1
            ok = False
            while not ok:
                mark = next
                next = self.text.index(mark + "+%d lines linestart" %
                                         lines_to_get)
                lines_to_get = min(lines_to_get * 2, 100)
                ok = "SYNC" in self.text.tag_names(next + "-1c")
                line = self.text.get(mark, next)
                if not line:
                    return
                #先移除所有标签
                self.RemoveTags(mark,next)
                chars = chars + line
                m = self.prog.search(chars)
                while m:
                    for key, value in m.groupdict().items():
                        if value:
                            a, b = m.span(key)
                            self.AddTag(head,a,b,key,value,chars)
                    m = self.prog.search(chars, m.end())
                if "SYNC" in self.text.tag_names(next + "-1c"):
                    head = next
                    chars = ""
                else:
                    ok = False
                if not ok:
                    # We're in an inconsistent state, and the call to
                    # update may tell us to stop.  It may also change
                    # the correct value for "next" (since this is a
                    # line.col string, not a true mark).  So leave a
                    # crumb telling the next invocation to resume here
                    # in case update tells us to leave.
                    self.text.tag_add("TODO", next)
                if self.stop_colorizing:
                    utils.get_logger().debug("colorizing stopped")
                    return
        self.text.after(1,self.text.update)

    def AddTag(self,head,match_start,match_end,key,value,chars):
        self.text.tag_add(key,
                     head + "+%dc" % match_start,
                     head + "+%dc" % match_end)

    def RemoveTags(self,start,end):
        for tag in self.tagdefs:
            self.text.tag_remove(tag, start, end)
