#TODO 第一步：定义工具函数
#定义工具类：位置>tools>custom_tool.py
#   1、将文本写入文档中
#   2、发送文本到邮件
#TODO 第二步：导包
import smtplib

from crewai import Agent, LLM, Task, Crew, Process
from tools.custom_tool import send_email,store_poesy_to_txt

#TODO 第三步：定义大语言模型
llm=LLM(model="ollama/qwen2.5:7b-instruct",base_url="http://127.0.0.1:11434")

#TODO 第四步：创建智能体
# 作家writer
# 编辑者editor
# 寄信者sender
#TODO 1、作家writer
wriwer=Agent(
    role="作家",#表明其主要功能
    goal="根据用户需求，创作出情感丰富的文章（最长不超过300个词）。",#目标
    backstory="""你作为一个著名的作家，拥有千万级别的粉丝，最擅长写情感类型的文章""",#角色设定
    verbose=True, #设置为True，者通常意味着代理将提供详细的日志、输出或解释
    allow_delegation=False,#设置为False，表示步允许此代理将其任务委派给其他代理或进程
    llm = llm
)
#TODO 2、编辑者editor
editor=Agent(
    role="内容编辑",
    goal="对作家撰写的文章内容进行精心编辑",
    backstory="""作为一名经验丰富的编辑，你在编辑书信方面由多年的经验，
    你需要将作家写的文章整理编排成书信样式，并将书信内容存储在本地磁盘上
    你必须使用tools列表中的store_poesy_to_txt工具，
    将编辑好的书信内容存储到指定文件中
    """,
    verbose=True,
    allow_delegation=False,
    tools=[store_poesy_to_txt],
    llm=llm
)
#TODO 3、寄信者sender
sender=Agent(
    role="寄信人",
    goal="将编辑好的书信以邮件的形式发送给心仪的人",
    backstory="""你作为一名专业的寄信人，在发送书信方面由多年的经验，
    请你把上边优化编辑好的情书发送给指定收件人，
    你必须使用tools列表中的send_email工具，并根据里边的sender_email、receiver_email等信息，
    将书信发送到指定邮箱
    """,
    verbose=True,
    allow_delegation=False,
    tools=[send_email],
    llm=llm
)

#TODO 第五步：定义用户需求
user_input=input("请输入您的写情书的要求或信息：")
receiver_email = input("请输入收件人的邮箱地址：")

#TODO 第六步：创建任务Task
# 写情书
# 编辑书信
# 寄信
#TODO 1、写情书
task1=Task(
    #任务描述
    description=f"""用户需求：{user_input},
    你最后给出的答案必须是一份富含爱情表示的情书。""",
    #期望输出结果描述
    expected_output="已经生成一份情感真挚的情书（300字左右）",
    #执行该任务的代理对象
    agent=wriwer
)

#TODO 2、编辑书信
task2=Task(
    #任务描述
    description=f"""查找任何语法错误，进行编辑和格式优化（如果需要）。
    并要求将内容保存在本地磁盘中。将内容保存到本地非常重要，
    你最后的答案必须是信息是否已被存储在本地磁盘中。""",
    #期望输出结果描述
    expected_output="已经编辑并优化好情书为书信格式，并成功保存到本地磁盘中",
    #执行该任务的代理对象
    agent=editor
)

#TODO 3、寄信
task3=Task(
    #任务描述
    description=f"""根据本次磁盘的保存的书信内容，你将整理并发送邮件给心仪的人，这个很重要。
    你最后的答案一定要成功发送该邮件。参数：to: {receiver_email}""",
    #期望输出结果描述
    expected_output="发送邮件任务已经调用成功，请查看邮箱",
    #执行该任务的代理对象
    agent=sender
)

#TODO 第七步：创建Crew对象，传入智能体和任务并触发运行
crew=Crew(
    agents=[wriwer,editor,sender],
    tasks=[task1,task2,task3],
    verbose=True,
    Process=Process.sequential #按顺序执行，Process.parallel是并发执行
)

#TODO 第八步：触发运行
result =crew.kickoff()

#TODO 第九步：打印结果
print(result)