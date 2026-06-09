#TODO 第一步：导包
import smtplib
from crewai.tools import tool
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from cryptography.x509 import name

#TODO 第二步：确定目标>定义两个函数
#函数一：实现将文本写入txt文档中>store_poesy_to_tet>content:str>str
#函数二：实现发送邮件到指定邮箱>send_email

#TODO 第三步：实现函数一
'''
@tool装饰器:
作用:将一个普通的 Python 函数，快速“包装”成一个可以被 AI 智能体（Agent）识别和调用的“工具”。
理解:给函数贴上了一个 “技能标签”。贴上这个标签后，CrewAI 框架就知道：“哦，这个函数是可以被 Agent 使用的工具”。
核心价值:
    1.  自动化: 自动根据函数名和文档字符串生成 `name` 和 `description`。
    2.  简化: 避免了编写繁琐的工具类代码。
使用方式:
    from crewai.tools import tool
    @tool
    def my_custom_function(input_param: str) -> str:
        """这里是工具的描述，AI 会根据它来决定是否调用。"""
        # 实现工具的具体逻辑
        return f"处理结果: {input_param}"
'''
#这里的description是（“”）里写的内容
#name默认为函数名store_poesy_to_txt
@tool("将编辑后的书信文本内容自动保存到txt文档中")
#TODO 1、定义函数（def → 文档 → try 体）
def store_poesy_to_txt(content: str) -> str:     #函数头
    #TODO 2、文档
    """
    将编辑后的书信文本内容自动保存到txt文档中
    :param content: 编辑后的书信文本内容
    :return: 返回写入完成的提示信息
    """
    """
    尝试执行里面的代码。如果过程中发生了任何错误（异常），程序不会崩溃，而是会跳转到 except 部分。
    使用 try-except 块捕获并优雅处理可能在文件写入过程中发生的异常（如磁盘空间不足、权限错误等），
    防止程序因未处理的异常而意外终止。
    """
    try:
        #TODO 3、定义txt文档的名称
        #注意这是一个固定文件名，每次调用都会覆盖这个文件。如果需要每次保存不同的文件，可以让 fileName 也作为一个参数。
        fileName="情书.txt"
        #TODO 4、将文本写入txt文档中，如不存在则自动创建
        '''
        - "w" 模式表示写入。如果文件已存在，会覆盖原有内容；如果不存在，会创建新文件。
        - encoding="utf-8" 确保中文能正确保存，不会乱码。
        - with 语句会在代码块执行完毕后，自动关闭文件，无需手动调用 file.close()。
        '''
        with open(fileName,"w",encoding="utf-8") as f:
            #将传入的 content 字符串写入到打开的文件中。
            f.write(content)
        #如果文件写入成功，返回一个成功的提示信息给 AI 智能体。
        return f"已将编辑后的文本内容自动保存到txt文档中：{fileName}"
    #捕获 try 块中发生的任何异常（比如文件无法写入、磁盘空间不足等），并将异常信息赋值给变量 e。
    except Exception as e:
        #向调用者（AI 智能体）返回一个友好的错误提示，而不是让程序直接报错停止。
        return f"写入txt文档时出错：{e}"

#TODO 第四步：实现函数二
@tool("将编辑后的书信文本内容发送到指定邮箱")
def send_email(to:str, subject: str, body: str):

    """
    将编辑后的书信文本内容发送到指定邮箱
    :param subject: 邮件主题
    :param body: 邮件正文内容
    :return: 返回发送完成的提示信息
    """
    #TODO 1、邮箱配置：
    #发件人
    sender_email = "zhangyang2312022@163.com"
    #发件人密码
    #这里只是为了快速验证实现，实际应用中，为了安全考虑，建议从环境变量中或配置文件中读取
    sender_pwd = "SXv5MkKLgZDhs4jD"
    #收件人
    # receiver_email = "1848607098@qq.com"
    # print(f"登录时使用的授权码是：{sender_pwd}")

    #TODO 2、邮件标题：
    subject="💌情书"
    #TODO 3、读取邮件内容
    with open("情书.txt","r",encoding="utf-8") as f:
        email_content = f.read()

    #TODO 4、邮件格式:
    #MIMEMultipart表示构建复杂的邮件格式
    #MIMEText表示纯文本文件
    msg = MIMEMultipart()
    #发件人地址-》from
    msg["From"] = sender_email
    #收件人地址-》to
    # msg["To"] = receiver_email
    msg["To"] = to
    #标题-》subject
    msg["Subject"] = subject
    #TODO 5、将邮件内容作为传闻本附件添加到邮件对象中
    #email_content：要发送的邮件正文内容，
    # "plain"：指定内容类型为纯文本格式，
    # "utf-8"：指定文本编码格式为UTF-8
    #该方法无返回值，直接修改message对象的内容
    # msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(email_content, "plain", "utf-8"))
    #TODO 为smtp_server设置初始值，
    # 以防在执行smtp_server.quit()时，因smtplib.SMTP_SSL(...) 这一行执行失败（比如网络不通、服务器拒绝连接），
    # 那么 smtp_server 这个变量就不会被成功创建
    # finally 块里却试图调用 smtp_server.quit()，此时 smtp_server 还不存在，程序就会报错
    smtp_server = None  # 加这一行
    #TODO try......excepy体
    try:
        #TODO 6、连接邮箱smtp服务器并发送邮件
        #"smtp.163.com"(服务器地址host），465（端口号，默认，port）
        smtp_server = smtplib.SMTP_SSL("smtp.163.com", 465)
        #TODO 7、建立连接
        smtp_server.connect("smtp.163.com", 465)
        smtp_server.login(sender_email, sender_pwd)
        #TODO 8、登录邮箱账号（传入发件人的邮件地址和授权码）
        #msg.as_string()：将邮件消息对象转换为字符串类似，以便STMP服务器发送
        #该方法无返回值，直接将邮件发送到STMP服务器
        # smtp_server.sendmail(sender_email, receiver_email, msg.as_string())
        smtp_server.sendmail(sender_email, to, msg.as_string())
        #TODO 9、发送成功提示
        print("邮件发送成功")
    except Exception as e:
        print("邮件发送失败！",f"发送邮件时出错：{e}")
    finally:
        if smtp_server:    # 只有当 smtp_server 成功创建后才关闭
            #TODO 关闭STMP连接，释放资源（这段代码不管成功与否，都要执行）
            smtp_server.quit()