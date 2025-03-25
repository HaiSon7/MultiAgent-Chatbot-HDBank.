from langchain_core.messages import HumanMessage,AIMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from agent_retriever import get_retriever
from langgraph.graph import MessagesState
from typing_extensions import TypedDict

# from agent_supervisor import supervisor_node

members = ['retriever', 'assistant']
gemma2_2btool = "cow/gemma2_tools:2b"
llama3_2 = "llama3.2:3b"
llama3_1 = "llama3.1"

llm_retriever = ChatOllama(model=llama3_2, temperature=0.2, streaming=True)
llm = ChatOllama(model=gemma2_2btool, temperature=0.5, streaming=True)
llm_sup = ChatOllama(model=llama3_1, temperature=0.3, streaming=True)
options = members + ["FINISH"]


class AgentState(MessagesState):
    next: str


retriever_agent = create_react_agent(
    llm_retriever, tools=[get_retriever],
    state_modifier="Bạn là một người truy xuất sản phẩm sau đó tổng hợp thông tin lại và trả về. Không làm gì khác."
)

assistant_prompt = """
    Bạn là Assistant AI, Nhân viên tư vấn khách hàng của HD Bank.
    Hãy trả lời ngắn dọn dựa trên các thông tin được cung cấp.
    Ở cuối câu trả lời luôn hỏi "Bạn có thắc mắc điều gì không ? 🤗"
"""

assistant_agent = create_react_agent(
    llm, tools=[], state_modifier=assistant_prompt
)


def assistant_node(state: AgentState) -> AgentState:
    result = assistant_agent.invoke(state)
    if result.get("messages"):
        response_content = result["messages"][-1].content
    else:
        response_content = "Không có kết quả."
    return {
        "messages": [
            AIMessage(content=response_content, name="assistant")
        ]
    }


def retriever_node(state: AgentState) -> AgentState:
    result = retriever_agent.invoke(state)
    if result.get("messages"):
        response_content = result["messages"][-1].content
    else:
        response_content = "Không có kết quả."
    return {
        "messages": [
            AIMessage(content=response_content, name="retriever")
        ]
    }


class Router(TypedDict):
    next: Literal[*options]


system_prompt = (
    "Bạn là người giám sát tư vấn khách hàng của ngân hàng HD Bank, "
    "Bạn giám sát và quản lý cuộc trò chuyện giữa những người sau : "
    f"{members}, "
    "Xác định nội dung yêu cầu của người dùng. Trả về ai là người thực hiện hành động tiếp theo, "
    "Mỗi member sẽ thực hiện và trả về kết quả và trạng thái. "
    "Nếu asisstant đã trả lời được người dùng, hãy trả về FINISH."
)
# system_prompt = (
#     "You are a supervisor tasked with managing a conversation between the"
#     f" following workers: {members}. Given the following user request,"
#     " respond with the worker to act next. Each worker will perform a"
#     " task and respond with their results and status. When finished,"
#     " respond with FINISH."
# )

def supervisor_node(state: AgentState) -> AgentState:
    messages = [
                   {"role": "system", "content": system_prompt},
               ] + state["messages"]

    response = llm_sup.with_structured_output(Router).invoke(messages)
    next_ = response["next"]

    # Log giá trị quyết định tiếp theo
    print(f"Supervisor decision: {next_}")

    if next_ == "FINISH":
        next_ = END
        print("Finishing conversation...")  # Log khi kết thúc

    return {"next": next_}


builder = StateGraph(MessagesState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("retriever", retriever_node)
builder.add_node("assistant", assistant_node)

for member in members:
    builder.add_edge(member, "supervisor")

builder.add_conditional_edges("supervisor", lambda state: state["next"])
builder.add_edge(START, "supervisor")

graph = builder.compile()

# Hiển thị và lưu hình ảnh đồ thị
from IPython.display import display, Image

display(Image(graph.get_graph().draw_mermaid_png()))
with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

# Chạy đồ thị với input
for s in graph.stream(
        {
            "messages": [
                (
                        "user",
                        "Xin chào",
                )
            ]
        },
        subgraphs=True,
):
    print(s)
    print("----")
