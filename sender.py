# coding=utf-8

import smtplib
from email.mime.text import MIMEText
from email.header import Header
import configparser, os

root_dir = os.getcwd()
cf = configparser.ConfigParser()
cf.read(root_dir + "/config.ini")
from_addr = cf.get("Email", "from_addr")
qqCode = cf.get("Email", "qqCode")
smtp_server = cf.get("Email", "smtp_server")
smtp_port = cf.get("Email", "smtp_port")


def send_mail(to_mail, novel_name, mail):
    stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
    stmp.login(from_addr, qqCode)
    # 组装发送内容
    message = MIMEText(mail, 'plain', 'utf-8')  # 发送的内容
    message['From'] = Header("小说更新系统", 'utf-8')  # 发件人
    message['To'] = Header("大王", 'utf-8')  # 收件人
    subject = novel_name
    message['Subject'] = Header(subject, 'utf-8')  # 邮件标题
    try:
        stmp.sendmail(from_addr, to_mail, message.as_string())
    except Exception as e:
        print('邮件发送失败--' + str(e))
    print('邮件发送成功')
