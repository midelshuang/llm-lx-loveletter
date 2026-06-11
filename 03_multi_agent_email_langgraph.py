#TODO 第一步：导包
import os #读取环境变量
from dotenv import load_dotenv #加载 .env 文件中的配置
from crewai import Agent, Task, Crew, LLM, Process  # 暂时还用 CrewAI 的 LLM 类，定义大语言模型（暂时复用 CrewAI 的，后面可替换）
from langgraph.graph import StateGraph, END #LangGraph 的核心：状态图和结束标志
from tools.custom_tool_v2 import send_email, store_poesy_to_txt #版本2中已经定义好的工具函数
from typing import TypedDict, List, Optional


'''
这里暂时用了 CrewAI 的 LLM 类。LangGraph 本身不依赖特定 LLM 封装，你可以用任何方式调用模型
'''
#TODO 第二步：加载环境变量
load_dotenv()

#TODO 第三步：定义 LLM
llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://127.0.0.1:11434"
)

#TODO 核心结构：定义状态 → 定义节点 → 构建图 → 执行

#TODO ========== 定义状态 ==========
from typing import TypedDict, List, Optional

#TODO 定义一个Agent状态类，参数是TypedDict，告诉 Python 和 IDE 这个字典里有哪些字段，以及每个字段的类型。这样写代码时会有自动补全。
class AgentState(TypedDict):
    """工作流的状态"""
    user_input: str  # 用户输入的情书要求，由主程序写入
    receiver_email: str  # 收件人邮箱，由主程序写入
    draft: Optional[str]  # 草稿（作家生成的初稿），由作家节点写入
    edited: Optional[str]  # 编辑润色后的终稿，由编辑节点写入
    save_result: Optional[str]  # 保存结果，由编辑节点写入
    email_result: Optional[str]  # 发送结果，由发送节点写入
    current_step: str  # 当前执行的步骤名，由各节点写入
    messages: List[dict]  # 消息历史（用于 LLM 调用），由各节点写入


#TODO ========== 节点函数 ==========
'''
节点函数的统一模式：
def 节点名(state: AgentState) -> AgentState:
    1. 从 state 中读取需要的数据
    2. 执行业务逻辑（调用 LLM、工具等）
    3. 将结果写入 state
    4. 返回更新后的 state
    return state
'''

#TODO 1、作家节点
def writer_node(state: AgentState) -> AgentState:
    """作家节点：根据用户需求创作情书"""
    print("\n📝 作家开始创作...")

    # 这里调用 LLM 生成情书
    # 为了简化，先用一个简单的 prompt，后续可以优化
    from crewai import Task, Agent

    #TODO (1) 创建一个临时 Agent
    writer_agent = Agent(
        role="作家",
        goal="根据用户需求创作情感丰富的文章（最长不超过300个词）",
        backstory="你是著名作家，擅长写情感文章",
        llm=llm,
        verbose=False
    )

    #TODO (2) 创建任务，使用 state 中的 user_input
    task = Task(
        description=f"用户需求：{state['user_input']}。请创作一封情书。",
        expected_output="一封情感真挚的情书",
        agent=writer_agent
    )

    #TODO (3) 创建一个临时 Crew 来执行这个任务
    crew = Crew(
        agents=[writer_agent],
        tasks=[task],
        verbose=False
    )

    # TODO (3) 执行任务，获取结果
    result = crew.kickoff()
    # crewai 0.201.1 中 result 是字符串，直接使用
    result_str = str(result) if result else "（未生成内容）"
    # result = task.execute()

    #TODO (4) 将结果写入 state
    state["draft"] = result_str
    state["current_step"] = "writer"

    #TODO (5) 添加消息历史
    '''
    为什么用 setdefault？
        state["messages"] 可能还不存在（第一次调用时），setdefault 会在没有时自动创建一个空列表。
    '''
    state.setdefault("messages", []).append({
        "role": "assistant",
        "content": f"作家已完成初稿：\n{result_str[:200]}..."
    })

    return state

#TODO 2、编辑节点
def editor_node(state: AgentState) -> AgentState:
    """编辑节点：编辑润色情书并保存到文件"""
    print("\n✏️ 编辑开始润色...")

    from crewai import Task, Agent

    editor_agent = Agent(
        role="内容编辑",
        goal="对文章进行精心编辑，优化格式和语法",
        backstory="经验丰富的编辑，擅长润色书信",
        tools=[store_poesy_to_txt],
        llm=llm,
        verbose=False
    )

    task = Task(
        description=f"""请编辑以下情书，优化格式和语法，然后调用 store_poesy_to_txt 工具保存到文件。

        情书内容：
        {state['draft']}
        """,
        expected_output="编辑后的情书和保存结果",
        agent=editor_agent
    )

    crew = Crew(
        agents=[editor_agent],
        tasks=[task],
        verbose=False,
        process=Process.sequential
    )

    result = crew.kickoff()
    result_str = str(result) if result else "（保存失败）"

    # result = task.execute()
    state["edited"] = result_str
    state["save_result"] = result_str
    state["current_step"] = "editor"

    state.setdefault("messages", []).append({
        "role": "assistant",
        "content": f"编辑已完成：{result_str[:200]}..."
    })

    return state

#TODO 3、发送节点
def sender_node(state: AgentState) -> AgentState:
    """发送节点：发送邮件"""
    print("\n📧 寄信人开始发送邮件...")

    from crewai import Task, Agent

    sender_agent = Agent(
        role="寄信人",
        goal="将编辑好的情书发送给收件人",
        backstory="专业的寄信人",
        tools=[send_email],
        llm=llm,
        verbose=False
    )

    body_content = state.get("edited") or state.get("draft") or "（无内容）"

    task = Task(
        description=f"""请调用 send_email 工具发送邮件。

        参数：
        - to: {state['receiver_email']}
        - subject: 💌情书
        - body: {state['edited'] or state['draft']}
        """,
        expected_output="邮件发送成功的确认信息",
        agent=sender_agent
    )

    crew = Crew(
        agents=[sender_agent],
        tasks=[task],
        verbose=False,
        process=Process.sequential
    )

    result = crew.kickoff()
    result_str = str(result) if result else "（发送失败）"

    # result = task.execute()
    state["email_result"] = result_str
    state["current_step"] = "sender"

    state.setdefault("messages", []).append({
        "role": "assistant",
        "content": result_str
    })

    return state


#TODO ========== 构建图 ==========
'''
StateGraph 的两种常见模式：
    模式	   | 说明	           | 代码
    线性顺序 |A → B → C	       |add_edge(A, B), add_edge(B, C)
    条件分支 |根据状态决定下一步	   |add_conditional_edges()
'''

def build_graph():
    """构建 LangGraph 工作流"""
    workflow = StateGraph(AgentState) # ← 创建一个状态图，指定状态类型

    #TODO 添加节点（每个节点就是一个处理单元）
    workflow.add_node("writer", writer_node) # 节点名 → 函数
    workflow.add_node("editor", editor_node)
    workflow.add_node("sender", sender_node)

    #TODO 添加边（定义节点之间的流转顺序）
    workflow.add_edge("writer", "editor") # writer 执行完 → 去 editor
    workflow.add_edge("editor", "sender") # editor 执行完 → 去 sender
    workflow.add_edge("sender", END)              # sender 执行完 → 结束

    #TODO 设置入口（第一个执行的节点）
    workflow.set_entry_point("writer")

    return workflow.compile() # 编译成可执行的应用


# ========== 主程序 ==========

if __name__ == "__main__":
    #TODO 1. 获取用户输入
    user_input = input("请输入您的写情书的要求或信息：")
    receiver_email = input("请输入收件人的邮箱地址：")

    #TODO 2. 初始化状态（只填充初始数据，其他字段留空）
    initial_state = AgentState(
        user_input=user_input,
        receiver_email=receiver_email,
        draft=None,
        edited=None,
        save_result=None,
        email_result=None,
        current_step="start",
        messages=[]
    )

    #TODO 3. 编译图
    app = build_graph()

    print("\n" + "=" * 50)
    print("开始执行情书生成工作流...")
    print("=" * 50)

    #TODO 4. 执行工作流
    final_state = app.invoke(initial_state)

    print("\n" + "=" * 50)
    print("工作流执行完成！")
    print("=" * 50)

    #TODO 5. 输出结果
    print(f"\n最终结果：{final_state['email_result']}")