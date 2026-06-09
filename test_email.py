import smtplib
from email.mime.text import MIMEText

# 你的邮箱配置
sender = "zhangyang2312022@163.com"
auth_code = "SXv5MkKLgZDhs4jD"
recipient = "1848607098@qq.com"

# 发送邮件
try:
    msg = MIMEText("这是一封测试邮件", "plain", "utf-8")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = "测试邮件"

    with smtplib.SMTP_SSL("smtp.163.com", 465) as server:
        server.login(sender, auth_code)
        server.sendmail(sender, [recipient], msg.as_string())
        print("邮件发送成功！")
except Exception as e:
    print(f"发送失败: {e}")