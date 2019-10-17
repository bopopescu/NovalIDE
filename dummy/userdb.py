from __future__ import print_function
import os
from dummy import sql
import datetime
from dummy.basedb import *
from noval.util import singleton
import noval.util.appdirs as appdirs
import noval.consts as consts
import getpass
import noval.util.apputils as apputils
import datetime
import noval.python.parser.utils as parserutils
import json
import noval.util.utils as utils
import noval.util.urlutils as urlutils
import noval.util.fileutils as fileutils

if apputils.is_windows():
    import wmi
    import pythoncom

    def get_host_info():
        pythoncom.CoInitialize()
        c = wmi.WMI ()
        os_name = ''
        os_bit = ''
        sn = ''
        try:
            for os_sys in c.Win32_OperatingSystem():
                os_name = os_sys.Caption.encode("UTF8").strip()
                os_bit = os_sys.OSArchitecture.encode("UTF8")
            for physical_disk in c.Win32_DiskDrive():
                sn = physical_disk.SerialNumber.strip()
        except Exception as e:
            utils.GetLogger().warn("get system info error:%s,will use external tool to get system info",e)
            get_system_tool_path = os.path.join(sysutilslib.mainModuleDir,"tools\\dummytool.exe")
            p = os.popen(get_system_tool_path)
            content = p.read()
            os_name_flag = "os name:"
            os_bit_flat = "os bit:"
            sn_flag = "serial number:"
            for line in content.splitlines():
                if line.find(os_name_flag) != -1:
                    os_name = line.replace(os_name_flag,"").strip()
                elif line.find(os_bit_flat) != -1:
                    os_bit = line.replace(os_bit_flat,"").strip()
                elif line.find(sn_flag) != -1:
                    sn = line.replace(sn_flag,"").strip()
        return os_name,os_bit,sn
else:
    import platform
    def get_host_info():
        os_name = platform.platform()
        os_bit = platform.architecture()[0]
        sn = 'unkown disk sn'
        r = os.popen("ls -l /dev/disk/by-uuid")
        content = r.read()
        for line in content.split('\n'):
            if line.find("->") != -1:
                sn = line.split()[8].strip()
                break
        return os_name,os_bit,sn

@singleton.Singleton
class UserDataDb(BaseDb):
    
    USER_DATA_DB_NAME = "data.db"
    DB_VERSION = "1.0.2"
    ###HOST_SERVER_ADDR = 'http://127.0.0.1:8000'
    HOST_SERVER_ADDR = 'http://www.novalide.com'
    ####HOST_SERVER_ADDR = 'http://47.105.90.123:8080/'

    def __init__(self):
        self.CheckDbVersion()
        db_dir = os.path.join(appdirs.get_user_data_path(),consts.USER_CACHE_DIR)
        if not os.path.exists(db_dir):
            parserutils.MakeDirs(db_dir)
        self.data_id = None
        self.user_id = None
        db_path = os.path.join(db_dir,self.USER_DATA_DB_NAME)
        BaseDb.__init__(self,db_path)
        self.init_data_db()
            
    def CheckDbVersion(self):
        db_dir = os.path.join(appdirs.get_user_data_path(),consts.USER_CACHE_DIR)
        db_file = os.path.join(db_dir,self.USER_DATA_DB_NAME)
        db_ver_file = os.path.join(db_dir,self.USER_DATA_DB_NAME + ".version")
        if self.NeedUpdateDatabaseFile(db_ver_file):
            if os.path.exists(db_file):
                utils.get_logger().info("the database file %s need to be updated",db_file)
                fileutils.safe_remove(db_file)
                if not os.path.exists(db_file):
                    self.SaveDbVersion(db_ver_file)
                else:
                    utils.get_logger().error("remove database file %s fail",db_file)
                    
    def SaveDbVersion(self,db_ver_file):
        with open(db_ver_file,"w") as f:
            return f.write(self.DB_VERSION)

    def NeedUpdateDatabaseFile(self,db_ver_file):
        if not os.path.exists(db_ver_file):
            return True
        if parserutils.CompareCommonVersion(self.DB_VERSION,self.GetDbVersion(db_ver_file)):
            utils.get_logger().info("the database version is updated......")
            return True
        return False

    def init_data_db(self):
        table_already_exist_flag = 'already exists'
        try:
            self.create_table(sql.CREATE_USER_TABLE_SQL,"user")
        except sqlite3.OperationalError as e:
            if str(e).find(table_already_exist_flag) == -1:
                print (e)
                return 

        try:
            self.create_table(sql.CREATE_USER_DATA_TABLE_SQL,"data")
        except sqlite3.OperationalError as e:
            if str(e).find(table_already_exist_flag) == -1:
                print (e)
                return 

    def CreateUser(self):
        os_name,os_bit,sn = get_host_info()
        insert_sql = '''
            insert into user(os_bit,os,sn,user_name) values (?,?,?,?)
        '''
        data = [(os_bit,os_name,sn,getpass.getuser())]
        self.save(insert_sql,data)
        
    def GetDbVersion(self,db_ver_file):
        with open(db_ver_file) as f:
            return f.read()

    def GetUser(self):
        sql = "select * from user"
        result = self.fetchone(sql)
        if not result:
            self.CreateUser()
            result = self.fetchone(sql)
        self.user_id = result[0]
        if result[1] == None:
            api_addr = '%s/member/getuser' % (self.HOST_SERVER_ADDR)
            sn = result[4]
            data = urlutils.RequestData(api_addr,arg = {'sn':sn})
            if data is not None and data['code'] != 0:
                api_addr = '%s/member/createuser' % (self.HOST_SERVER_ADDR)
                sn = result[4]
                args = {
                    'sn':sn,
                    'os_bit':result[3],
                    'os_name':result[5],
                    'user_name':result[2],
                    'app_version':apputils.get_app_version()
                }
                data = urlutils.RequestData(api_addr,arg = args,method='post')
            if data is not None and data['code'] == 0:
                member_id = data['member_id']
                update_sql = '''
                    update user set user_id='%s' where id=%d
                ''' % (member_id,self.user_id )
                self.update(update_sql)
        
    def RecordStart(self):
        self.GetUser()
        insert_sql = '''
            insert into data(user_id,app_version) values (?,?)
        '''
        data = [(self.user_id,utils.get_app_version()),]
        self.data_id = self.save(insert_sql,data)
        
    def RecordEnd(self):
        if self.data_id is None or self.user_id is None:
            return
        update_sql = '''
            update data set end_time='%s' where id=%d
        ''' % (datetime.datetime.now(),self.data_id )
        self.update(update_sql)
        
    def QueryRecord(self):
        sql = "select * from data where id=%d" % self.data_id
        for result in self.fetchall(sql):
            print (result)
            
    def GetMemberId(self,user_id):
        sql = "select * from user where id=%d" % user_id
        result = self.fetchone(sql)
        if not result:
            return None
        return result[1]
            
    def ShareUserData(self):
        sql = "select * from data"
        for result in self.fetchall(sql):
            if not result[3]:
                api_addr = '%s/member/share_data' % (self.HOST_SERVER_ADDR)
                member_id = self.GetMemberId(result[1])
                if not member_id:
                    continue
                args = {
                    'member_id':member_id,
                    'start_time':result[4],
                    'end_time':result[5],
                    'app_version':result[2],
                }
                data = urlutils.RequestData(api_addr,arg = args,method='post')
                if data is not None and data['code'] == 0:
                    update_sql = '''
                        update data set submited=1 where id=%d
                    ''' % result[0]
                    self.update(update_sql)
            else:
                delete_sql = '''
                delete from data where id=%d
                '''%result[0]
                self.delete(delete_sql)
        
    def GetUserId(self):
        sql = "select * from user"
        result = self.fetchone(sql)
        if not result:
            return None
        return result[1]
        
    def GetUserInfo(self):
        sql = "select * from user"
        result = self.fetchone(sql)
        return result