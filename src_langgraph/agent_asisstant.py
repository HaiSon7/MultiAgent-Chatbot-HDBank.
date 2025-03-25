from langchain_core.messages import HumanMessage,AIMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from agent_retriever import get_retriever
from langgraph.graph import MessagesState
from typing_extensions import TypedDict
import sys
import time

# from agent_supervisor import supervisor_node

members = ['retriever_product','assistant']
gemma2_2btool = "cow/gemma2_tools:2b"
llama3_2 = "llama3.2:3b"
llama3_1 = "llama3.1"

llm_retriever = ChatOllama(model=llama3_2, temperature=0.2, streaming=True)
llm = ChatOllama(model=gemma2_2btool, temperature=0.5, streaming=True)
llm_sup = ChatOllama(model=llama3_2, temperature=0.3, streaming=True)
options = members + ["FINISH"]
class AgentState(MessagesState):
    next: str
class Router(TypedDict):
    next: Literal["retriever_product", "assistant", "FINISH"]

retriever_product_agent = create_react_agent(
    llm_retriever, tools=[get_retriever],
    state_modifier="""Bạn là một người truy xuất sản phẩm sau đó tổng hợp thông tin lại và trả về. 
                    Nếu không tìm thấy thông tin thì trả về không thấy.
                   Không làm gì khác."""
)

def retriever_product_node(state: AgentState) -> AgentState:
    result = retriever_product_agent.invoke(state)
    
    if result.get("messages"):
        response_content = result["messages"][-1].content
    else:
        response_content = "Không có kết quả."
    
    return {
        "messages": state["messages"] + [
            AIMessage(content=response_content, name="retriever_product")
        ]
    }


assistant_prompt = """
    Bạn là Assistant AI, Nhân viên tư vấn khách hàng của HD Bank.
    Hãy trả lời ngắn dọn dựa trên các thông tin được cung cấp.
"""

assistant_agent = create_react_agent(
    llm, tools=[], state_modifier=assistant_prompt
)
def assistant_node(state: AgentState) -> AgentState:
    result = assistant_agent.invoke(state)
    if result.get("messages"):
        response_content = result["messages"][-1].content
        if not response_content.strip():  # Kiểm tra nếu response trống
            response_content = "Xin lỗi, tôi không hiểu. Bạn có thể nói rõ hơn được không?"
    else:
        response_content = "Xin lỗi, tôi không hiểu. Bạn có thể nói rõ hơn được không?"
    
    return {
        "messages": state["messages"] + [
            AIMessage(content=response_content, name="assistant")
        ]
    }




system_prompt = (
    f"""Bạn là Assistant AI của HD Bank, Bạn giám sát các {members} . 
    Dựa vào yêu cầu của người dùng bạn quyết định xem ai là người hành động tiếp theo. 
    Mỗi member sẽ trả về kết quả và trạng thái.
    Khi hoàn thành hãy trả về FINISH .
    Bạn chỉ được phản hồi một trong các {options}.
    """
)

def supervisor_node(state: AgentState) -> AgentState:
    try:
        # Lấy toàn bộ lịch sử hội thoại
        conversation_history = "\n".join([
            f"{'User' if isinstance(m, HumanMessage) else m.name}: {m.content}"
            for m in state["messages"]
        ])
        
        # Kiểm tra xem đã có response cho message hiện tại chưa
        current_message_responded = False
        messages = state["messages"]
        if len(messages) >= 2:  # Có ít nhất 1 cặp user-assistant
            last_user_idx = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
            current_message_responded = any(
                isinstance(m, AIMessage) 
                for m in messages[last_user_idx+1:]
            )
        
        # Nếu đã có response, kết thúc
        if current_message_responded:
            return {"next": END}
            
        # Prompt để phân loại với ví dụ cụ thể
        classify_prompt = f"""
        Dưới đây là lịch sử hội thoại. Hãy phân loại yêu cầu mới nhất của người dùng:

        Lịch sử hội thoại:
        {conversation_history}

        Phân loại thành một trong hai loại:
        1. CHAT: 
           - Câu chào hỏi (ví dụ: xin chào, chào bạn, hi)
           - Hỏi thông tin cá nhân của bot (ví dụ: bạn tên gì, bạn là ai)
           - Small talk (ví dụ: thời tiết thế nào, bạn khỏe không)
           - Câu trả lời yes/no đơn giản
           - Cảm ơn, tạm biệt
           - Các câu hỏi KHÔNG liên quan đến sản phẩm/dịch vụ ngân hàng

        2. QUERY: 
           - Câu hỏi về sản phẩm ngân hàng (ví dụ: thẻ tín dụng, khoản vay)
           - Câu hỏi về dịch vụ ngân hàng (ví dụ: cách mở tài khoản)
           - Câu hỏi về chính sách, lãi suất, phí
           - Câu hỏi follow-up về thông tin đã được cung cấp
           - Yêu cầu giải thích chi tiết về sản phẩm/dịch vụ
           - Các câu hỏi CẦN TRA CỨU thông tin từ ngân hàng

        CHÚ Ý: 
        - CHỈ TRẢ VỀ MỘT TỪ DUY NHẤT "CHAT" HOẶC "QUERY" (VIẾT HOA)
        - Nếu câu hỏi KHÔNG liên quan đến sản phẩm/dịch vụ ngân hàng thì là CHAT
        - Câu hỏi về thông tin cá nhân của bot (tên, tuổi, etc) là CHAT
        """
        
        response = llm_sup.invoke(classify_prompt)
        raw_response = response.content if hasattr(response, 'content') else str(response)
        
        if "CHAT" in raw_response.upper():
            question_type = "CHAT"
        elif "QUERY" in raw_response.upper():
            question_type = "QUERY"
        else:
            question_type = "CHAT"
        
        print(f"Question type: {question_type}")
        
        if question_type == "CHAT":
            return {"next": "assistant"}
        return {"next": "retriever_product"}
        
    except Exception as e:
        print(f"Error in supervisor_node: {e}")
        return {"next": END}


# Sửa lại phần xây dựng graph
builder = StateGraph(MessagesState)

# Add nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("retriever_product", retriever_product_node)
builder.add_node("assistant", assistant_node)

# Add edges
builder.add_edge(START, "supervisor")

# Định nghĩa route_step
def route_step(state: AgentState) -> str:
    return state["next"]

# Add conditional edges
builder.add_conditional_edges(
    "supervisor",
    route_step,
    {
        "retriever_product": "retriever_product",
        "assistant": "assistant",
        END: END
    }
)

# Add edges từ các nodes về supervisor
builder.add_edge("retriever_product", "supervisor")
builder.add_edge("assistant", "supervisor")

# Compile graph
graph = builder.compile()

# Thêm vào cuối file, sau phần compile graph

def print_streaming(text: str, delay: float = 0.02):
    """In text theo kiểu streaming với delay giữa các ký tự"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write('\n')
    sys.stdout.flush()

def chat_loop():
    print_streaming("Bot: Xin chào! Tôi là AI trợ lý của HD Bank. Bạn cần giúp gì ạ?")
    print_streaming("(Gõ 'quit' để thoát)")
    print("-" * 50)
    
    while True:
        try:
            # Nhận input từ user
            user_input = input("Bạn: ").strip()
            
            # Kiểm tra điều kiện thoát
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print_streaming("Bot: Tạm biệt bạn! Hẹn gặp lại!")
                break
                
            # Khởi tạo state mới cho mỗi lượt chat
            state = {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            }
            
            # Theo dõi response cuối cùng để in ra
            last_response = None
            
            # Stream responses
            for step in graph.stream(state):
                # Lấy messages từ step output nếu có
                if isinstance(step, dict):
                    for value in step.values():
                        if isinstance(value, dict) and "messages" in value:
                            messages = value["messages"]
                            if messages and isinstance(messages[-1], AIMessage):
                                last_response = messages[-1]
            
            # In response cuối cùng với streaming effect
            if last_response and last_response.content.strip():
                sys.stdout.write("Bot: ")
                sys.stdout.flush()
                print_streaming(last_response.content, delay=0.02)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n")
            print_streaming("Bot: Tạm biệt bạn! Hẹn gặp lại!")
            break
        except Exception as e:
            print(f"Có lỗi xảy ra: {e}")
            print_streaming("Bot: Xin lỗi, có lỗi xảy ra. Bạn có thể thử lại không?")
            print("-" * 50)

# Tùy chỉnh delay cho các loại nội dung khác nhau
def print_streaming_smart(text: str):
    """
    In text với delay thông minh dựa vào dấu câu
    """
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Delay dài hơn cho dấu câu
        if char in ['.', '!', '?']:
            time.sleep(0.1)
        # Delay trung bình cho dấu phẩy và chấm phẩy
        elif char in [',', ';']:
            time.sleep(0.05)
        # Delay ngắn cho các ký tự khác
        else:
            time.sleep(0.02)
    sys.stdout.write('\n')
    sys.stdout.flush()

# Chạy chat loop thay vì single message
if __name__ == "__main__":
    # Hiển thị và lưu hình ảnh đồ thị
    from IPython.display import display, Image
    display(Image(graph.get_graph().draw_mermaid_png()))
    with open("graph_test.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())
        
    # Bắt đầu chat loop
    chat_loop()
