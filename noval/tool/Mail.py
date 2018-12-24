import wx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import noval.util.utils as utils
from Crypto.PublicKey import RSA
import binascii
from Crypto.Cipher import PKCS1_v1_5
from noval.dummy.userdb import UserDataDb
import os
from noval.tool.consts import _

receive_list = ['kan.wu@genetalks.com']

class RsaCrypto():
    def __init__(self):
        with open(get_priviate_key_path()) as f:
            self.private_key = f.read()
    
    def decrypt(self, hex_data):
        private_key = RSA.import_key(self.private_key)
        cipher_rsa = PKCS1_v1_5.new(private_key)
        en_data = binascii.unhexlify(hex_data.encode('utf-8'))
        data = cipher_rsa.decrypt(en_data, None).decode('utf-8')
        return data
        
def get_priviate_key_path():
    priviate_key_path = os.path.join(utils.GetUserDataPath(),"cache","private_key")
    return priviate_key_path
            
def get_mail_credential():
    api_addr = UserDataDb.HOST_SERVER_ADDR + "member/get_mail"
    priviate_key_path = get_priviate_key_path()
    is_private_key_exist = False
    if os.path.exists(priviate_key_path):
        is_private_key_exist = True
    result = utils.RequestData(api_addr,arg={'is_load_private_key':int(not is_private_key_exist)},to_json=True)
    if result is None:
        wx.MessageBox(_("could not connect to server"),style=wx.OK|wx.ICON_ERROR)
        return None,-1,None,None,None,False
    if not is_private_key_exist:
        private_key = result['private_key']
        with open(priviate_key_path,"w") as f:
            f.write(private_key)
    return result['sender'],int(result['port']),result['smtpserver'],result['user'],result['password'],False
    
def send_mail(subject,content):

    sender,port,smtpserver,username,encrypt_password,use_tls = get_mail_credential()
    if sender is None:
        utils.GetLogger().error('send mail fail')
        return False
    password = RsaCrypto().decrypt(encrypt_password)
    msg = MIMEMultipart()

    puretext = MIMEText(content,_subtype='plain',_charset='utf8')
    msg.attach(puretext)

    msg['Subject'] = subject 
    msg['From'] =  'NovalIDE'
    msg['To'] = ";".join(receive_list)
    
    #log_attach = MIMEApplication(open(file_name, 'rb').read())
   # log_attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_name))
    #msg.attach(log_attach)

    smtp = smtplib.SMTP()
    smtp.connect(smtpserver,port=port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(sender, receive_list, msg.as_string())
    smtp.quit()
    utils.GetLogger().info('send mail success')
    return True
