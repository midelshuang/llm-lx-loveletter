#TODO 第一步：导包
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from crewai.tools import tool
from dotenv import load_dotenv

#TODO 第二步：加载 .env 文件中的环境变量
load_dotenv()

#TODO 第三步：实现函数一
@tool("将编辑后的书信文本内容自动保存到txt文档中")
def store_poesy_to_txt(content: str) -> str:
    """将编辑后的书信文本内容自动保存到txt文档中"""
    try:
        #TODO 从环境变量（.env文件）读取文件名，如果没设置则使用默认值
        file_name = os.getenv("FILE_NAME", "情书.txt")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已将编辑后的文本内容自动保存到txt文档中：{file_name}"
    except Exception as e:
        return f"写入txt文档时出错：{e}"

#TODO 第四步：实现函数二
@tool("将编辑后的书信文本内容发送到指定邮箱")
def send_email(to: str, subject: str, body: str) -> str:
    """
    将编辑后的书信文本内容发送到指定邮箱
    :param to: 收件人邮箱地址
    :param subject: 邮件主题
    :param body: 邮件正文内容
    :return: 返回发送完成的提示信息
    """
    #TODO 从环境变量读取邮箱配置
    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_PWD")

    #TODO 优先使用传入的 body，如果为空则从文件读取（兼容两种调用方式）
    email_content = body if body else "未提供邮件内容"

    # 构建邮件
    msg = MIMEMultipart()
    msg["From"] = sender_email
    #TODO 不使用默认收信者，而是让用户输入，作为to参数传入
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(email_content, "plain", "utf-8"))

    smtp_server = None
    try:
        smtp_server = smtplib.SMTP_SSL("smtp.163.com", 465)
        smtp_server.login(sender_email, sender_pwd)
        smtp_server.sendmail(sender_email, to, msg.as_string())
        print("邮件发送成功")
        return f"邮件已成功发送给 {to}，主题：{subject}"
    except Exception as e:
        print(f"邮件发送失败：{e}")
        return f"邮件发送失败：{e}"
    finally:
        if smtp_server:
            smtp_server.quit()