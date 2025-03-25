from langchain_core.messages import HumanMessage, AIMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from agent_retriever import get_retriever
from langgraph.graph import MessagesState
from typing_extensions import TypedDict
from agent_tavily_search import tavily_search
from datetime import datetime

# Constants
members = ['retriever_product', 'assistant','searcher']
gemma2_2b = "gemma2:2b"
llama3_2 = "llama3.2:3b"
llama3_1 = "llama3.1"
gemma2_tools= "cow/gemma2_tools:2b"
# Initialize LLMs directly

llm_shared = ChatOllama(model=llama3_2, temperature=0.2, streaming=True)
llm = ChatOllama(model=gemma2_2b, temperature=0.3, streaming=True)
llm_retriever = llm_shared
llm_sup = llm_shared
llm_search = llm_shared
# Type definitions
class AgentState(MessagesState):
    next: str

class Router(TypedDict):
    next: Literal["retriever_product", "assistant","searcher", "FINISH"]
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)
def supervisor_node(state: AgentState) -> AgentState:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm_sup.with_structured_output(Router).invoke(messages)
    next_ = response["next"]
    if next_ == "FINISH":
        next_ = END

    return {"next": next_}

retriever_product_agent = create_react_agent(
        llm_retriever, tools=[get_retriever],
        state_modifier ="""
        BẠN LÀ NGƯỜI TRUY XUẤT THÔNG TIN. KHÔNG CẦN TRẢ LỜI NGƯỜI DÙNG.
        XÁC ĐỊNH SẢN PHẨM NGƯỜI DÙNG MUỐN HỎI.
        NẾU TÌM THẤY TRẢ VỀ TOÀN BỘ THÔNG TIN TÌM ĐƯỢC.
        NẾU KHÔNG TÌM THẤY ĐÚNG SẢN PHẨM THÌ BẮT BUỘC TRẢ VỀ "NO RESULT".
        KHÔNG LÀM GÌ KHÁC.
        """
    )
searcher_agent = create_react_agent(
    llm_search,tools = [tavily_search],
    state_modifier="""
        Search Thông tin mới nhất liên quan tới HDBank,
        Trả về thông tin liên quan và đầy đủ nhất.
    """
)
assistant_prompt = """
    Bạn là Assistant AI, Nhân viên tư vấn khách hàng của Ngân hàng thương mại cổ phần Phát triển Thành phố Hồ Chí Minh HD Bank.
    KHÔNG ĐƯỢC TỰ TRẢ LỜI NẾU KHÔNG CÓ THÔNG TIN SẢN PHẨM.
    ĐẢM BẢO TRẢ LỜI NGẮN GỌN DỰA TRÊN THÔNG TIN ĐƯỢC CUNG CẤP.
"""

assistant_agent = create_react_agent(
    llm, tools=[], state_modifier=assistant_prompt
)


def searcher_node(state: AgentState) -> AgentState:
    result = searcher_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="researcher")
        ]
    }

def retriever_product_node(state: AgentState) -> AgentState:
    result = retriever_product_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="researcher")
        ]
    }

def assistant_node(state: AgentState) -> AgentState:
    result = assistant_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="researcher")
        ]
    }


builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("searcher", searcher_node)
builder.add_node("retriever_product", retriever_product_node)
builder.add_node("assistant", assistant_node)
builder.add_edge(START, "supervisor")


for member in members:
    # We want our workers to ALWAYS "report back" to the supervisor when done
    builder.add_edge(member, "supervisor")

# The supervisor populates the "next" field in the graph state
# which routes to a node or finishes
builder.add_conditional_edges("supervisor", lambda state: state["next"])

graph = builder.compile()


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