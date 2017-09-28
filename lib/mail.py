# -*- coding: utf-8 -*-
import sys, os, time, random
import yaml
import smtplib
from email import encoders
from email.header import Header
from email.utils import parseaddr, formataddr
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase

from lib.baseClass import AbstractClass
import lib.appPath


class SMTPMail(AbstractClass):
    def __init__(self, fromEmail, fromEmailPassword, toEmail, smtpServer, smtpPort=25):
        super(self.__class__, self).__init__()
        self.fromEmail = fromEmail
        self.fromEmailPassword = fromEmailPassword
        self.toEmail = toEmail
        self.smtpServer = smtpServer
        self.smtpPort = smtpPort

    @classmethod
    def get_config(cls):
        config = {}
        config_path = os.path.join(lib.appPath.CONFIG_PATH, 'mail.yml');
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'SMTP' in profile:
                    mail_config = profile['SMTP']
                    if 'fromEmail' in mail_config:
                        config['fromEmail'] = mail_config['fromEmail']
                    if 'fromEmailPassword' in mail_config:
                        config['fromEmailPassword'] = mail_config['fromEmailPassword']
                    if 'toEmail' in mail_config:
                        config['toEmail'] = mail_config['toEmail']
                    if 'smtpServer' in mail_config:
                        config['smtpServer'] = mail_config['smtpServer']
                    if 'smtpPort' in mail_config:
                        config['smtpPort'] = mail_config['smtpPort']
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                lib.diagnose.check_python_import('smtplib'))

    def _formatAddr(cls,s): 
    	name, addr = parseaddr(s) 
    	return formataddr((
    		Header(name, 'utf-8').encode(),
    		addr.encode('utf-8') if isinstance(addr, unicode) else addr))

    def sendImageEmail(self,image):
    	msg = MIMEMultipart('related')
    	msg['Subject'] = Header(u'来自机器人C(weedge)的邮件，请查看', 'utf-8').encode()
    	msg['From'] = self._formatAddr(u'小C(weedge)  <%s>' % self.fromEmail)
    	msg['To'] = self._formatAddr(u'主人邮箱 <%s>' % self.toEmail)
    
    	#邮件内容
    	msg.attach(MIMEText('Hi,您好,监控文件见附件', 'plain', 'utf-8'))
    
    	#图片附件
    	mime = MIMEBase('image', 'jpg', filename='img.jpg')
    	# 加上必要的头信息:
    	mime.add_header('Content-Disposition', 'attachment', filename='img.jpg')
    	mime.add_header('Content-ID', '<0>')
    	mime.add_header('X-Attachment-Id', '0')
    	mime.set_payload(image)
    	# 用Base64编码:
    	encoders.encode_base64(mime)
    	# 添加到MIMEMultipart:
    	msg.attach(mime)
    
    	smtp = smtplib.SMTP(self.smtpServer, self.smtpPort)
    	smtp.set_debuglevel(1)
    	#smtp.starttls()
    	smtp.login(self.fromEmail, self.fromEmailPassword)
    	smtp.sendmail(self.fromEmail, self.toEmail, msg.as_string())
    	smtp.quit()
