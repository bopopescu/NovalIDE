#This file was originally generated by NovalIDE's unitest wizard
import unittest
import noval.tool.interpreter.Interpreter
import noval.util.utils as utils
import noval.util.logger as logger
import time

from html.parser import HTMLParser  
class PyPiHtmlParser(HTMLParser):  
    a_text = False  
      
    def handle_starttag(self,tag,attr):  
        if tag == 'a':  
            self.a_text = True  
              
    def handle_endtag(self,tag):  
        if tag == 'a':  
            self.a_text = False  
              
    def handle_data(self,data):  
        if self.a_text:  
            api_addr = "https://pypi.org//pypi/%s/json" % data
            print data,utils.RequestData(api_addr,to_json=True)

class TestInterpreter(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def testName(self):
        pass

class TestPythonInterpreter(unittest.TestCase):
    def setUp(self):
        logger.initLogging()
        #self.intrepreter = noval.tool.Interpreter.PythonInterpreter('tttt',"c:\\python26\python.exe")
    def tearDown(self):
        pass

    def testGetVersion(self):
        pass

    def ____testCheckSyntax(self):
        print self.intrepreter.Version
        print self.intrepreter.IsV27()
        print self.intrepreter.IsV26()
        print self.intrepreter.CheckSyntax(r"D:\env\Noval\noval\test\ast_test_file.py")

    def testHelpPath(self):
        pass

    def testDefault(self):
        pass

    def testGetSyspathList(self):
        pass

    def testGetBuiltins(self):
        pass

    def testSetInterpreterInfo(self):
        pass

    def testAnalysing(self):
        pass

    def testIsAnalysed(self):
        pass
        

    def testPipSource(self):
        
        source_list = [
            "https://pypi.org/simple",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "http://mirrors.aliyun.com/pypi/simple",
            "https://pypi.mirrors.ustc.edu.cn/simple",
            "http://pypi.hustunique.com",
            "http://pypi.sdutlinux.org",
            "http://pypi.douban.com/simple"
        ]
        
        for pip_source in source_list:
            #api_addr = pip_source
            #print pip_source,utils.RequestData(api_addr,{})
            api_addr = pip_source + "/ok"
            start = time.time()
            if utils.RequestData(api_addr,timeout=10,to_json=False):
                end = time.time()
                elapse = end - start
                print api_addr,elapse
                
    def testGetAllPipPackages(self):
        
        pip_source = "https://pypi.org/simple"
        
        contents = utils.RequestData(pip_source,to_json=False)
        html_parser = PyPiHtmlParser()  
        html_parser.feed(contents)  
        html_parser.close()  
        #for line in contents.splitlines():
         #   print line,"---------------"
         
    def testGetPipProjectInfo(self):
        
        api_addr = "https://pypi.org//pypi/%s/json" % "libaws"
        print utils.RequestData(api_addr,to_json=True)
        
        api_addr = "https://pypi.org//pypi/%s/json" % "codecounter"
        print utils.RequestData(api_addr,to_json=True)
    

class TestInterpreterManager(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def testLoadDefaultInterpreter(self):
        pass

    def testChooseDefaultInterpreter(self):
        pass

    def testGetInterpreterByName(self):
        pass

    def testLoadPythonInterpreters(self):
        pass

    def testLoadPythonInterpretersFromConfig(self):
        pass

    def testConvertInterpretersToDictList(self):
        pass

    def testSavePythonInterpretersConfig(self):
        pass

    def testAddPythonInterpreter(self):
        pass

    def testRemovePythonInterpreter(self):
        pass

    def testSetDefaultInterpreter(self):
        pass

    def testMakeDefaultInterpreter(self):
        pass

    def testGetDefaultInterpreter(self):
        pass

    def testGetChoices(self):
        pass

    def testGetInterpreterById(self):
        pass

    def testCheckInterpreterExist(self):
        pass

    def testCheckIdExist(self):
        pass

    def testGenerateId(self):
        pass

    def testIsInterpreterAnalysing(self):
        pass

    def testSetCurrentInterpreter(self):
        pass

    def testGetCurrentInterpreter(self):
        pass

class TestInterpreterAddError(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test__str__(self):
        pass

class TestGlobalFunction(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def testGetCommandOutput(self):
        pass


if __name__ == "__main__":
    unittest.main()