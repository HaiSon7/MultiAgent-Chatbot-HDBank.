from typing import Literal
from typing_extensions import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END

gemma2_9b = "gemma2:latest"
gemma2_2b = "gemma2:2b"
gemma2_2btool="cow/gemma2_tools:2b"
llama3_2 = "llama3.2"

members = ['retriever','asisstant']
options = members + ["FINISH"]
system_prompt = (
    "Bạn là người giám sát và quản lý cuộc trò chuyện giữa "
    f"{members[0]} và {members[1]} ,"
    f"Nếu người dùng không hỏi về sản phẩm bạn hãy  trả về {members[1]} ,"
    f"Nếu yêu cầu của người dùng hỏi về sản phẩm hãy trả về  {members[0]} , "
    " Mỗi member sẽ thực hiện và trả về kết quả và trạng thái."
    " Khi hoàn thành, hãy trả về FINISH "
)
llm = ChatOllama(model=llama3_2,
                    temperature = 0.5,
                    streaming = True
                     )


class AgentState(MessagesState):
    # The 'next' field indicates where to route to next
    next: str

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]

def supervisor_node(llm,state: AgentState) -> AgentState:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    next_ = response["next"]
    if next_ == "FINISH":
        next_ = END

    return {"next": next_}