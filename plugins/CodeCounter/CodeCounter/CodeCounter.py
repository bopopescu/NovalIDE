import sys
import os
import datetime
import filerange
import argparse
import yaml


PARSER_CONFIG_FILE = "parser.yml"

class CommentFlag(object):
    def __init__(self,line_comment_flag,block_comment_start_flag=None,block_comment_end_flag=None):
        self.line_comment_flag = line_comment_flag
        self.block_comment_start_flag = block_comment_start_flag
        self.block_comment_end_flag = block_comment_end_flag
    
    def __str__(self):
     
        str = "line comment:%s block comment start:%s block coment end:%s" % (self.line_comment_flag,self.block_comment_start_flag,self.block_comment_end_flag)
        return str
    
class Parser(object):
    def __init__(self,parse_id,ext_list_str,line_comment_flag,block_comment_start_flag=None,block_comment_end_flag=None):
        self.parser_id = parse_id
        if ext_list_str != "":
            self.ext_list = ext_list_str.split(',')
        else:
            self.ext_list = []
        self.comment_flag = CommentFlag(line_comment_flag,block_comment_start_flag,block_comment_end_flag)
    
    def is_ext_enable(self,ext):
        ext = ext.lower()
        if ext in self.ext_list:
            return True
        return False
    
    def __str__(self):
        str = "id:%d ext list:%s %s" % (self.parser_id,self.ext_list,self.comment_flag)
        return str
    
    def is_filename_confirm(self,special_file_name):
        return False
    
    @classmethod
    def get_parser_by_ext(cls,ext):
        
        for parser_id in ALL_PARSERS:
            parser = ALL_PARSERS[parser_id]
            if parser.is_ext_enable(ext):
                return parser
        
        return None
    
    @classmethod
    def get_parser_by_filename(cls,filename):
        
        for parser_id in ALL_PARSERS:
            parser = ALL_PARSERS[parser_id]
            if parser.is_filename_confirm(filename):
                return parser
        
        return None

class SpecialFileNameParser(Parser):
    
    def __init__(self,parse_id,file_name,line_comment_flag,block_comment_start_flag=None,block_comment_end_flag=None):
        super(SpecialFileNameParser,self).__init__(parse_id,'',line_comment_flag,block_comment_start_flag,block_comment_end_flag)
        self.file_name = file_name
        
    def is_filename_confirm(self,special_file_name):
        return self.file_name == special_file_name
        
ALL_PARSERS = {
}

def is_comment_line(line,line_comment_flag):
    if line_comment_flag == None:
        return False
    
    line = line.lstrip()
    if line.startswith(line_comment_flag):
        return True
    return False

def is_block_comment_start(line,block_comment_start_flag):
    if block_comment_start_flag == None:
        return False

    return is_comment_line(line,block_comment_start_flag)

def is_block_comment_end(line,block_comment_end_flag):
    if block_comment_end_flag == None:
        return False

    line = line.rstrip()
    if line.endswith(block_comment_end_flag):
        return True
    return False
    
def count_file_line(file_path,is_comment_exclude,is_blank_line_exclude,parser=None):
    
    comment_flag_parser = None
    if is_comment_exclude:
        if parser is None:
            filename = os.path.basename(file_path)
            ext = os.path.splitext(filename)[1].lower()
            parser = Parser.get_parser_by_ext(ext)
            if parser is None:
                parser = Parser.get_parser_by_filename(filename)
        if None != parser: 
            comment_flag_parser = parser.comment_flag
        
    count = 0
    with open(file_path) as f:
        is_block_line_range = False
        for line in f:
            if is_comment_exclude and comment_flag_parser != None:
                if is_comment_line(line,comment_flag_parser.line_comment_flag):
                    continue                
                elif is_block_comment_start(line,comment_flag_parser.block_comment_start_flag):
                    is_block_line_range = True
                    continue
                elif is_block_comment_end(line,comment_flag_parser.block_comment_end_flag):
                    is_block_line_range = False
                    continue
                elif is_block_line_range:
                    continue
            if is_blank_line_exclude:
                line = line.strip()
                if line == "":
                    continue
            count += 1

    print file_path,"code line count is:",count
    return count


def count_dir_file_lines(dir_path,is_comment_exclude,is_blank_line_exclude,exclude_dirs=[],exclude_files=[]):
    
    def is_dir_exclude(path,exclude_dirs):
        
        if path in exclude_dirs:
            return True
        
        loop_path = os.path.dirname(root)
        while loop_path:
            if loop_path in exclude_dirs:
                return True
            parent_path = os.path.dirname(loop_path)
            if parent_path == loop_path:
                break
            loop_path = parent_path
        
        return False
    
    def is_file_exclude(full_file_path,dir_path,exclude_dirs,exclude_files):
        
        if full_file_path in exclude_files:
            return True
        
        if is_dir_exclude(dir_path,exclude_dirs):
            return True
        
        return False
    
    total_line_count = 0
    total_file_count = 0
    for root,dirnames,filenames in os.walk(dir_path):
        root = os.path.abspath(root)
        for filename in filenames:
            full_file_path = os.path.join(root,filename)
            ext = os.path.splitext(filename)[1].lower()
            parser = Parser.get_parser_by_filename(filename)
            if None == parser:
                parser = Parser.get_parser_by_ext(ext)
                if None == parser:
                    continue
            if is_file_exclude(full_file_path,root,exclude_dirs,exclude_files):
                continue
            
            total_line_count += count_file_line(full_file_path,is_comment_exclude,is_blank_line_exclude,parser)
            total_file_count += 1
    print 'total code file count is:',total_file_count,',total code line count is:',total_line_count
    
def load_all_parsers():

    global ALL_PARSERS
    dir_path = os.path.abspath(os.path.split(__file__)[0])
    parser_config_path = os.path.join(dir_path,PARSER_CONFIG_FILE)
    f = open(parser_config_path)
    lang_config_list = yaml.load(f)
    f.close()

    #import json
    #print json.dumps(lang_config_list,indent=4)

    for lang_config in lang_config_list:
        lang_config = lang_config['lang']
        lang_id = lang_config['id']
        line_comment = lang_config['line_comment']
        block_comment_start = lang_config.get('block_comment_start',None)
        block_comment_end = lang_config.get('block_comment_end',None)
        if lang_config.has_key('filename'):
            special_file_name = lang_config['filename']
            parser = SpecialFileNameParser(lang_id,special_file_name,line_comment,block_comment_start,block_comment_end)
        else:
            ext = lang_config['ext']
            parser = Parser(lang_id,ext,line_comment,block_comment_start,block_comment_end)

        ALL_PARSERS[lang_id] = parser

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("-ignore-comment",type=int, dest="is_comment_exclude",help='indicate count the comment line or not',default = True)
    parser.add_argument("-ignore-blank-line",type=int, dest="is_blank_line_exclude",help='indicate count the blank line or not',default = True)
    parser.add_argument('-exclude-dir', action='append',dest='exclude_dirs',default=[],help='Add exclude dir to a list')
    parser.add_argument('-exclude-file', action='append',dest='exclude_files',default=[],help='Add exclude file to a list')
    args = parser.parse_args()
    path = args.path

    load_all_parsers()

    if os.path.isfile(path):
        count_file_line(path,args.is_comment_exclude,args.is_blank_line_exclude)
    elif os.path.isdir(path):
        count_dir_file_lines(path,args.is_comment_exclude,args.is_blank_line_exclude,args.exclude_dirs,args.exclude_files)
        
if __name__ == "__main__":
    main()
