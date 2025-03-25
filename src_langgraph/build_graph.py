from typing import Dict, Any, Optional, TypedDict, Literal, List
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from advanced_retriever import get_retriever
from agent_tavily_search import tavily_search
from cache_manager import ProductCache
import logging
from typing_extensions import NotRequired
import sys
import datetime

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tăng giới hạn đệ quy cho xử lý đồ thị phức tạp
sys.setrecursionlimit(10000)

# Định nghĩa các hằng số cho model và cấu hình
MODELS = {
    'llm_shared': "llama3.2:3b",  # Model dùng chung cho retriever và searcher
    'llm_assistant': "gemma2:2b",  # Model cho assistant
    'llm_supervisor': "llama3.2:3b",  # Model cho phân tích ngữ cảnh
    'temperature_default': 0.3,
    'temperature_retriever': 0.2,
    'temperature_supervisor': 0.2
}


# Định nghĩa schema cho state của agent
class AgentState(TypedDict):
    messages: list[HumanMessage | AIMessage]  # Tin nhắn hiện tại
    conversation_history: list[HumanMessage | AIMessage]  # Toàn bộ lịch sử
    next: NotRequired[str]  # Hành động tiếp theo
    current_info: NotRequired[str]  # Thông tin hiện tại
    context_type: NotRequired[str]  # Loại ngữ cảnh (PRODUCT/OTHER)
    cached_info: NotRequired[str]  # Thông tin từ cache
    context_metadata: NotRequired[Dict[str, Any]]# Metadata về ngữ cảnh (thời gian, chủ đề, etc.


class RouterOutput(TypedDict):
    next: Literal["product_cache", "retriever", "searcher", "assistant", "FINISH"]


class ContextAnalyzer:
    def __init__(self, llm_sup: ChatOllama, cache_manager: ProductCache):
        self.llm_sup = llm_sup
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)

    def analyze_query(self, state: Dict[str, Any]) -> str:
        try:
            conversation_history = state.get("conversation_history", [])
            current_messages = state.get("messages", [])
            current_query = current_messages[-1].content if current_messages else ""

            # Tạo prompt phân tích chuyên sâu về ngân hàng
            analysis_prompt = f"""Là chuyên gia phân tích yêu cầu của khách hàng, hãy phân loại yêu cầu sau:
            === LỊCH SỬ HỘI THOẠI ===
            {self._build_conversation_context(conversation_history)}
            === YÊU CẦU HIỆN TẠI ===
            {current_query}
            
            Dựa trên lịch sử cuộc trò chuyện,
            Nếu hỏi về sản phẩm, dịch vụ, thẻ, lãi xuất,.... trả về PRODUCT, 
            Nếu câu hỏi là nói chuyện thông thường thì trả về OTHER
            Chỉ trả về một từ: PRODUCT hoặc OTHER(Không cần giải thích)"""

            # Phân tích với LLM
            response = self.llm_sup.invoke(analysis_prompt)
            classification = response.content.strip().upper()

            # Log chi tiết quá trình phân tích
            self.logger.info(f"Query: {current_query}")
            self.logger.info(f"Phân loại: {classification}")

            # Cập nhật context metadata
            context_metadata = state.get("context_metadata", {})
            context_metadata.update({
                "last_query_type": classification,
                "query_timestamp": datetime.time,
                "query_content": current_query
            })
            state["context_metadata"] = context_metadata

            # Trả về hướng xử lý
            if "PRODUCT" in classification:
                self.logger.info(f"Chuyển câu hỏi '{current_query}' đến product_cache")
                return "product_cache"
            else:
                self.logger.info(f"Chuyển câu hỏi '{current_query}' đến assistant")
                return "assistant"

        except Exception as e:
            self.logger.error(f"Lỗi trong quá trình phân tích: {str(e)}")
            # Trong trường hợp lỗi, ưu tiên chuyển về product_cache để đảm bảo không bỏ sót thông tin quan trọng
            return "product_cache"

    def _build_conversation_context(self, history: List[Any]) -> str:
        """
        Xây dựng ngữ cảnh từ lịch sử một cách có cấu trúc.
        """
        context_parts = []
        recent_history = history[-5:] if history else []  # Lấy 5 tin nhắn gần nhất

        for msg in recent_history:
            role = "Người dùng" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content.strip()
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    def _update_conversation_context(self, state: Dict[str, Any], classification: str):
        """
        Cập nhật thông tin ngữ cảnh sau mỗi phân tích.
        """
        context = state.get("context_metadata", {})
        current_messages = state.get("messages", [])
        current_query = current_messages[-1].content if current_messages else ""

        # Cập nhật metadata ngữ cảnh
        context.update({
            "last_classification": classification,
            "last_query": current_query,
            "timestamp": datetime.time,
            "query_count": context.get("query_count", 0) + 1
        })

        # Nếu là query về sản phẩm, lưu lại để theo dõi flow
        if "PRODUCT" in classification:
            context["last_product_query"] = current_query
            context["product_query_count"] = context.get("product_query_count", 0) + 1

        state["context_metadata"] = context

class GraphBuilder:
    """Xây dựng và quản lý đồ thị xử lý đa tác tử"""

    def __init__(self):
        self.cache_manager = ProductCache()

        try:
            # Khởi tạo các model LLM
            self.llm_shared = ChatOllama(
                model=MODELS['llm_shared'],
                temperature=MODELS['temperature_default']
            )
            self.llm_assistant = ChatOllama(
                model=MODELS['llm_assistant'],
                temperature=MODELS['temperature_default']
            )
            self.llm_supervisor = ChatOllama(
                model=MODELS['llm_supervisor'],
                temperature=0.5
            )

            self.context_analyzer = ContextAnalyzer(self.llm_supervisor, self.cache_manager)
            self.create_agents()

        except Exception as e:
            logger.error(f"Lỗi khởi tạo GraphBuilder: {str(e)}")
            raise

    def create_agents(self):
        """Khởi tạo các agent với vai trò cụ thể"""
        try:
            # Retriever agent - tìm kiếm trong cơ sở dữ liệu nội bộ
            self.retriever_agent = create_react_agent(
                self.llm_shared,
                tools=[get_retriever],
                state_modifier="""
                Check title của sản phẩm với yêu cầu của người dùng.
                NẾU KHÔNG TÌM THẤY ĐÚNG SẢN PHẨM TRẢ VỀ " NO RESULT ".
                NẾU TÌM THẤY ĐÚNG SẢN PHẨM TRẢ VỀ TOÀN BỘ THÔNG TIN .
                 Không làm gì khác.
                """
            )

            # Searcher agent - tìm kiếm từ nguồn bên ngoài
            self.searcher_agent = create_react_agent(
                self.llm_shared,
                tools=[tavily_search],
                state_modifier="""
                BẠN LÀ AGENT TÌM KIẾM TRỰC TUYẾN:
                1. Chỉ tìm trên website HDBank
                2. Tập tung thông tin sản phẩm/dịch vụ
                3. TRẢ VỀ TOÀN BỘ THÔNG TIN BAO GỒM CẢ URL.
                4. KHÔNG CẦN LÀM GÌ KHÁC.
                """
            )

            # Assistant agent - tương tác với người dùng
            self.assistant_agent = create_react_agent(
                self.llm_assistant,
                tools=[],
                state_modifier="""
                BẠN LÀ AI ASSISTANT CỦA HDBANK:
                1. Đảm bảo tuyệt đối trả lời dựa trên thông tin được cung cấp
                2. Nếu không có thông tin: Thông báo không đủ thông tin
                3. Giọng điệu thân thiện, chuyên nghiệp
                4. Trả lời ngắn gọn, dễ hiểu
                """
            )

            logger.info("Khởi tạo agents thành công")

        except Exception as e:
            logger.error(f"Lỗi khởi tạo agents: {str(e)}")
            raise

    def create_nodes(self):
        """Tạo các node xử lý cho từng agent"""

        def product_cache_node(state: AgentState) -> AgentState:
            """Node kiểm tra cache thông tin sản phẩm"""

            try:
                query = state["messages"][-1].content
                logger.info(f"Tìm kiếm trong cache cho query: {query}")

                cache_hit, cached_info = self.cache_manager.find_matching_info(query)

                if cache_hit:
                    logger.info("Tìm thấy thông tin trong cache")
                    return {
                        "messages": state["messages"],
                        "cached_info": cached_info,
                        "next": "assistant"
                    }
                else:
                    logger.info("Không tìm thấy trong cache, chuyển sang retriever")
                    return {
                        "messages": state["messages"],
                        "next": "retriever"
                    }

            except Exception as e:
                logger.error(f"Lỗi tại product_cache: {str(e)}")
                return {"next": "retriever"}

        def retriever_node(state: AgentState) -> AgentState:
            """
            Node tìm kiếm trong database với logic xử lý kết quả cải tiến.
            Đảm bảo không chuyển sang searcher khi đã tìm thấy kết quả hợp lệ.
            """
            try:
                logger.info("Bắt đầu tìm kiếm trong database")
                result = self.retriever_agent.invoke(state)

                # Kiểm tra kết quả từ retriever
                if result and "messages" in result:
                    # Lấy tin nhắn cuối cùng là ToolMessage chứa kết quả tìm kiếm
                    messages = result["messages"]
                    for msg in reversed(messages):
                        if isinstance(msg, ToolMessage):
                            retriever_result = json.loads(msg.content)

                            # Kiểm tra kết quả có hợp lệ không
                            if retriever_result and len(retriever_result) > 0:
                                first_result = retriever_result[0]

                                # Kiểm tra nội dung có phải NO RESULT không
                                if first_result.get("content") != "NO RESULT":
                                    logger.info("Tìm thấy thông tin hợp lệ trong database")

                                    # Lưu vào cache và chuyển cho assistant
                                    self.cache_manager.add_to_cache(
                                        state["messages"][-1].content,
                                        first_result["content"]
                                    )

                                    return {
                                        "messages": state["messages"],
                                        "cached_info": first_result["content"],
                                        "next": "assistant"
                                    }

                    # Nếu không tìm thấy kết quả hợp lệ hoặc kết quả là NO RESULT
                    logger.info("Không tìm thấy thông tin hợp lệ, chuyển sang searcher")
                    return {
                        "messages": state["messages"],
                        "next": "searcher"
                    }

                logger.info("Không nhận được kết quả từ retriever, chuyển sang searcher")
                return {
                    "messages": state["messages"],
                    "next": "searcher"
                }

            except Exception as e:
                logger.error(f"Lỗi tại retriever node: {str(e)}")
                return {
                    "messages": state["messages"],
                    "next": "searcher"
                }

        def _validate_retriever_result(result: Dict) -> bool:
            """
            Hàm kiểm tra tính hợp lệ của kết quả từ retriever.
            """
            if not result or "content" not in result:
                return False

            content = result["content"]

            # Kiểm tra nội dung có ý nghĩa
            if not content or content == "NO RESULT":
                return False

            # Kiểm tra độ dài tối thiểu
            if len(content.strip()) < 50:  # Yêu cầu ít nhất 50 ký tự
                return False

            return True

        def searcher_node(state: AgentState) -> AgentState:
            """Node tìm kiếm từ nguồn bên ngoài"""
            try:
                logger.info("Bắt đầu tìm kiếm từ nguồn bên ngoài")
                result = self.searcher_agent.invoke(state)
                response = result.get("messages", [])[-1].content if result.get("messages") else None

                if response and "NO RESULT" not in response.upper():
                    logger.info("Tìm thấy thông tin từ nguồn bên ngoài")
                    self.cache_manager.add_to_cache(state["messages"][-1].content, response)
                    return {
                        "messages": state["messages"],
                        "cached_info": response,
                        "next": "assistant"
                    }
                else:
                    logger.info("Không tìm thấy thông tin từ mọi nguồn")
                    return {
                        "messages": state["messages"],
                        "next": "assistant"
                    }

            except Exception as e:
                logger.error(f"Lỗi tại searcher: {str(e)}")
                return {"next": "assistant"}

        def assistant_node(state: AgentState) -> AgentState:
            """Node xử lý câu trả lời cho người dùng"""
            try:
                cached_info = state.get("cached_info")
                current_messages = state.get("messages", [])
                conversation_history = state.get("conversation_history", [])
                conversation_context = self._build_conversation_context(conversation_history)
                # Nếu là câu hỏi thông thường, xử lý trực tiếp
                if not cached_info:
                    prompt = f"""Yêu cầu của người dùng :{current_messages[-1].content if current_messages else ""}"""
                    print(prompt)
                else:
                    # Nếu có thông tin sản phẩm, sử dụng để trả lời
                    prompt = f"""Yêu cầu của người dùng :{current_messages[-1].content if current_messages else ""},
                    Trả lời dựa trên thông tin sau:{cached_info}
                    Hãy trả lời câu hỏi của người dùng một cách ngắn gọn và chuyên nghiệp.
                    """


                result = self.assistant_agent.invoke({
                    "messages": conversation_history + [HumanMessage(content=prompt)]
                })
                response = result.get("messages", [])[-1].content if result.get(
                    "messages") else "Xin lỗi, tôi không thể xử lý yêu cầu này."
                updated_history = conversation_history + [
                    HumanMessage(content=current_messages[-1].content),
                    AIMessage(content=response)
                ]
                return {
                    "messages": current_messages + [AIMessage(content=response)],
                    "conversation_history": updated_history
                }

            except Exception as e:
                logger.error(f"Lỗi ở assistant node: {str(e)}")
                return {
                    "messages": current_messages + [
                        AIMessage(content="Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu của bạn.")
                    ]
                }

        return product_cache_node, retriever_node, searcher_node, assistant_node

    def _build_conversation_context(self, history: List) -> str:
        """
        Xây dựng ngữ cảnh hội thoại từ lịch sử một cách có cấu trúc.

        Args:
            history: Danh sách các tin nhắn trong lịch sử

        Returns:
            str: Ngữ cảnh được định dạng để assistant dễ hiểu
        """
        context_parts = []

        for i, msg in enumerate(history[-7:], 1):  # Chỉ lấy 5 tin nhắn gần nhất
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content.strip()
            context_parts.append(f"{role}: {content}")

        return "\n\n".join(context_parts)
    def build(self) -> StateGraph:
        """Xây dựng và trả về đồ thị hoàn chỉnh"""
        try:
            # Tạo các node xử lý
            product_cache_node, retriever_node, searcher_node, assistant_node = self.create_nodes()

            # Khởi tạo đồ thị
            builder = StateGraph(AgentState)

            # Thêm các node
            builder.add_node("product_cache", product_cache_node)
            builder.add_node("retriever", retriever_node)
            builder.add_node("searcher", searcher_node)
            builder.add_node("assistant", assistant_node)

            # Supervisor node
            def supervisor_node(state: AgentState) -> RouterOutput:
                """Node phân loại và điều hướng câu hỏi"""
                try:
                    if not state.get("messages"):
                        return {"next": "FINISH"}

                    current_query = state["messages"][-1].content
                    context = self.context_analyzer.analyze_query(state)

                    logger.info(f"Phân loại query: {context}")
                    logger.info(f"Query content: {current_query}")

                    # Đảm bảo mọi câu hỏi về sản phẩm đều đi qua product_cache
                    if "PRODUCT" in context.upper():
                        logger.info("Chuyển đến product_cache để tìm thông tin sản phẩm")
                        return {
                            "messages": state["messages"],
                            "next": "product_cache"
                        }
                    else:
                        logger.info("Chuyển đến assistant cho câu hỏi thông thường")
                        return {
                            "messages": state["messages"],
                            "next": "assistant"
                        }

                except Exception as e:
                    logger.error(f"Lỗi tại supervisor: {str(e)}")
                    return {"next": "FINISH"}

            builder.add_node("supervisor", supervisor_node)

            # Thêm edges
            builder.add_edge(START, "supervisor")

            # Conditional edges từ supervisor
            builder.add_conditional_edges(
                "supervisor",
                lambda state: state["next"],
                {
                    "product_cache": "product_cache",
                    "assistant": "assistant",
                    "FINISH": END
                }
            )

            # Conditional edges từ product_cache
            builder.add_conditional_edges(
                "product_cache",
                lambda state: state["next"],
                {
                    "retriever": "retriever",
                    "assistant": "assistant"
                }
            )

            # Conditional edges từ retriever
            builder.add_conditional_edges(
                "retriever",
                lambda state: state["next"],
                {
                    "searcher": "searcher",
                    "assistant": "assistant"
                }
            )

            # Conditional edges từ searcher
            builder.add_conditional_edges(
                "searcher",
                lambda state: state["next"],
                {
                    "assistant": "assistant"
                }
            )

            # Edge từ assistant về supervisor
            builder.add_edge("assistant", "supervisor")

            # Biên dịch đồ thị
            graph = builder.compile()
            logger.info("Biên dịch đồ thị thành công")
            return graph

        except Exception as e:
            logger.error(f"Lỗi khi xây dựng đồ thị: {str(e)}")
            raise

    def _validate_state(self, state: AgentState) -> bool:
        """
        Kiểm tra tính hợp lệ của trạng thái.

        Args:
            state: Trạng thái cần kiểm tra

        Returns:
            bool: True nếu trạng thái hợp lệ, False nếu không
        """
        try:
            required_fields = ["messages"]
            return all(field in state for field in required_fields)
        except Exception as e:
            logger.error(f"Lỗi kiểm tra trạng thái: {str(e)}")
            return False

    def _format_response(self, response: str) -> str:
        """
        Định dạng câu trả lời để đảm bảo tính nhất quán.

        Args:
            response: Câu trả lời gốc

        Returns:
            str: Câu trả lời đã được định dạng
        """
        try:
            # Loại bỏ khoảng trắng thừa
            response = response.strip()

            # Đảm bảo câu trả lời kết thúc bằng dấu chấm
            if response and not response.endswith(('.', '!', '?')):
                response += '.'

            # Định dạng các bullet points nếu có
            lines = response.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip().startswith(('-', '*', '•')):
                    formatted_lines.append('  ' + line.strip())
                else:
                    formatted_lines.append(line)

            return '\n'.join(formatted_lines)
        except Exception as e:
            logger.error(f"Lỗi định dạng response: {str(e)}")
            return response

    def _handle_timeout(self, max_retries: int = 3, timeout: int = 30) -> None:
        """
        Xử lý timeout cho các request.

        Args:
            max_retries: Số lần thử lại tối đa
            timeout: Thời gian chờ tối đa (giây)
        """
        import time
        from functools import wraps

        def timeout_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs, timeout=timeout)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"Hết số lần thử lại sau {max_retries} lần: {str(e)}")
                            raise
                        logger.warning(f"Lần thử {attempt + 1} thất bại, đang thử lại...")
                        time.sleep(1)

            return wrapper

        return timeout_decorator


def build_graph() -> StateGraph:
    """
    Hàm chính để xây dựng và trả về đồ thị xử lý đa tác tử.

    Returns:
        StateGraph: Đồ thị đã được cấu hình với các node và edges

    Raises:
        Exception: Nếu có lỗi trong quá trình xây dựng đồ thị
    """
    try:
        # Khởi tạo logging
        logger.info("Bắt đầu xây dựng đồ thị xử lý")

        # Tạo instance của GraphBuilder
        builder = GraphBuilder()

        # Xây dựng đồ thị
        graph = builder.build()

        # Kiểm tra đồ thị đã được xây dựng thành công
        if not graph:
            raise ValueError("Không thể xây dựng đồ thị")

        logger.info("Xây dựng đồ thị thành công")
        return graph

    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi khởi tạo đồ thị: {str(e)}")
        raise


# if __name__ == "__main__":
#     try:
#         # Thiết lập logging chi tiết hơn cho môi trường phát triển
#         logging.basicConfig(
#             level=logging.DEBUG,
#             format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#             handlers=[
#                 logging.StreamHandler(),
#                 logging.FileHandler('graph_builder.log')
#             ]
#         )
#
#         # Xây dựng đồ thị
#         graph = build_graph()
#     #
#     #     # Test đồ thị với một số câu hỏi mẫu
#     #     test_queries = [
#     #         "Xin chào",
#     #         "Cho tôi biết về sản phẩm thẻ tín dụng",
#     #         "Lãi suất vay hiện tại là bao nhiêu?",
#     #         "Cảm ơn"
#     #     ]
#     #
#     #     logger.info("Bắt đầu test đồ thị với các câu hỏi mẫu")
#     #
#     #     for query in test_queries:
#     #         try:
#     #             state = {"messages": [HumanMessage(content=query)]}
#     #             result = graph.invoke(state)
#     #             logger.info(f"Query: {query}")
#     #             logger.info(
#     #                 f"Response: {result.get('messages', [])[-1].content if result.get('messages') else 'No response'}")
#     #         except Exception as e:
#     #             logger.error(f"Lỗi khi test query '{query}': {str(e)}")
#     #
#     #     logger.info("Hoàn thành test đồ thị")
#     #
#     except Exception as e:
#         logger.error(f"Lỗi khi chạy chương trình: {str(e)}")
#         raise