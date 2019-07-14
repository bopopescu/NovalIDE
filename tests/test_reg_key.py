#This file was originally generated by NovalIDE's unitest wizard
from __future__ import print_function
import unittest
import noval.util.registry as registry

class TestRegistry(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test__init__(self):
        pass

    def testOpen(self):
        reg = registry.Registry()
        assert (reg.Open("kkkkkkk") is None)

    def testRead(self):
        reg = registry.Registry()
        child_reg = reg.Open(r"SOFTWARE\Python\Pythoncore")
        for reg_key in child_reg.EnumChildKey():
            print (reg_key.Read('InstallPath'))

        print (reg.Open(r"SOFTWARE").Read('NovalIDEDebug'),"++++++++++++")
        child_reg = reg.Open(r"SOFTWARE\NovalIDEDebug\RecentFiles")
        print (child_reg.ReadEx(r"file1"),"==================")
        print (child_reg.ReadEx("MDIFrameMaximized"))
        print (child_reg.ReadEx("PrimaryFont"))
        
    def testEnumChildKey(self):
        pass

    def testEnumChildKeyNames(self):
        reg = registry.Registry()
        child_reg = reg.Open(r"SOFTWARE\Python\Pythoncore")
        for name in child_reg.EnumChildKeyNames():
            print (name)
            
        reg = registry.Registry(registry.HKEY_LOCAL_MACHINE)
        child_reg = reg.Open(r"SOFTWARE\Python\Pythoncore")
        assert(child_reg is None)

    def testDeleteKey(self):
        reg = registry.Registry()
        child_reg = reg.Open(r"SOFTWARE\NovalIDEDebug")
        child_reg.DeleteKey('xxxx/yyy/zzz/ddd')
        child_reg.DeleteKey('xxxx\\yyy')
        child_reg.DeleteKey('xxxx\\yyy\\zzz\\ddd')

    def testDeleteValue(self):
        reg = registry.Registry()
        child_reg = reg.Open(r"SOFTWARE\NovalIDEDebug")
        print (child_reg.RootKey)
        child_reg.DeleteValue('ShowTipAtStartup')

    def testCreateKey(self):
        reg = registry.Registry()
        child_reg = reg.Open(r"SOFTWARE\NovalIDEDebug")
        new_key = child_reg.CreateKey('xxxx')
        new_key.WriteValue("","abc")
        new_key.WriteValue("","abcdef")
        new_key.WriteValue("test_reg_sz","12345")
        new_key.WriteValueEx("test_reg_sz","12345")
        
        new_key.WriteValueEx("demo_int",123,registry.REG_DWORD)
        
        child_reg.CreateKey('xxxx/yyy/zzz/ddd')
        child_reg.CreateKeys('xxxx/yyy/zzz/ddd')

    def test_with_key(self):
        reg = registry.Registry()
        with reg.Open(r"SOFTWARE\NovalIDEDebug") as reg:
            print (reg.ReadEx('ShowTipAtStartup'),"===============")

if __name__ == "__main__":
    unittest.main()