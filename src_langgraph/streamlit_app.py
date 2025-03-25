import streamlit as st
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
import os
from pathlib import Path
from build_graph import GraphBuilder, build_graph


def setup_logging():
    """
    Thiết lập hệ thống logging chi tiết để theo dõi luồng xử lý và debug.
    Tạo cấu trúc thư mục logs và đặt tên file theo ngày.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Tạo tên file log với timestamp
    log_file = log_dir / f"chatbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Cấu hình logging với nhiều mức độ chi tiết
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


class HDBANKChatInterface:
    """
    Giao diện chat thông minh cho HDBANK với khả năng xử lý ngữ cảnh
    và phân tích hội thoại nâng cao.
    """

    def __init__(self):
        # Thiết lập tin nhắn chào mừng
        self.welcome_message = """
        👋 Xin chào! Tôi là Trợ lý AI của HDBank.

        Tôi có thể giúp bạn:
        • Tư vấn về sản phẩm và dịch vụ ngân hàng
        • Cung cấp thông tin về lãi suất và biểu phí
        • Giải đáp thắc mắc về thẻ tín dụng, tài khoản
        • Hướng dẫn các thủ tục, quy trình giao dịch
        • Cập nhật ưu đãi và chương trình khuyến mãi mới

        Hãy đặt câu hỏi hoặc chia sẻ nhu cầu của bạn!
        """

        # Khởi tạo giao diện và trạng thái
        self.configure_page()
        self.initialize_session_state()

        # Khởi tạo GraphBuilder với xử lý ngữ cảnh
        self.initialize_graph_builder()

    def configure_page(self):
        """Cấu hình giao diện Streamlit với style hiện đại và responsive"""
        st.set_page_config(
            page_title="HDBank AI Assistant",
            page_icon="🏦",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # CSS tùy chỉnh cho giao diện
        st.markdown("""
        <style>
        /* Container chính */
        .main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Style cho tin nhắn */
        .chat-message {
            padding: 1.5rem;
            border-radius: 0.8rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            animation: fadeIn 0.5s ease-out;
        }

        /* Tin nhắn người dùng */
        .user-message {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }

        /* Tin nhắn assistant */
        .assistant-message {
            background-color: #f5f5f5;
            border-left: 4px solid #9e9e9e;
        }

        /* Hiệu ứng loading */
        .stSpinner {
            text-align: center;
            padding: 2rem;
        }

        /* Animation cho tin nhắn mới */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .chat-message {
                padding: 1rem;
                margin: 0.5rem 0;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def initialize_session_state(self):
        """
        Khởi tạo và quản lý trạng thái phiên làm việc.
        Theo dõi lịch sử hội thoại và thông tin ngữ cảnh.
        """
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": self.welcome_message
            }]

        if "conversation_context" not in st.session_state:
            st.session_state.conversation_context = {
                "current_topic": None,
                "last_product_query": None,
                "interaction_count": 0,
                "context_history": []
            }

        if "graph_builder" not in st.session_state:
            try:
                st.session_state.graph_builder = GraphBuilder()
                st.session_state.graph = st.session_state.graph_builder.build()
                logger.info("Khởi tạo graph thành công")
            except Exception as e:
                logger.error(f"Lỗi khởi tạo graph: {str(e)}")
                st.error("Không thể khởi tạo hệ thống chat. Vui lòng thử lại sau.")

    def initialize_graph_builder(self):
        """
        Khởi tạo GraphBuilder với các tính năng xử lý ngữ cảnh.
        Cấu hình các thành phần và tham số cho hệ thống multi-agent.
        """
        try:
            if "graph_builder" not in st.session_state:
                graph_builder = GraphBuilder()
                st.session_state.graph = graph_builder.build()
                st.session_state.graph_builder = graph_builder
                logger.info("Khởi tạo GraphBuilder thành công")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo GraphBuilder: {str(e)}")
            st.error("Không thể khởi tạo hệ thống. Vui lòng thử lại.")

    def update_conversation_context(self, user_input: str, response: str):
        """
        Cập nhật ngữ cảnh hội thoại dựa trên tương tác mới.
        Phân tích và lưu trữ thông tin ngữ cảnh quan trọng.
        """
        context = st.session_state.conversation_context
        context["interaction_count"] += 1

        # Thêm tương tác mới vào lịch sử
        context["context_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "interaction_number": context["interaction_count"]
        })

        # Giới hạn kích thước lịch sử
        max_history = 10
        if len(context["context_history"]) > max_history:
            context["context_history"] = context["context_history"][-max_history:]

    def process_message(self, user_input: str) -> Optional[str]:
        """
        Xử lý tin nhắn người dùng thông qua hệ thống multi-agent có ngữ cảnh.

        Args:
            user_input: Câu hỏi hoặc yêu cầu của người dùng

        Returns:
            Optional[str]: Câu trả lời từ hệ thống
        """
        try:
            if not hasattr(st.session_state, "graph"):
                logger.error("Graph chưa được khởi tạo")
                return "Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau."

            # Lấy lịch sử hội thoại từ session state
            conversation_history = [
                msg for msg in st.session_state.messages
                if msg["role"] in ["user", "assistant"]
            ]

            # Chuyển đổi format tin nhắn
            formatted_history = []
            for msg in conversation_history:
                if msg["role"] == "user":
                    formatted_history.append(HumanMessage(content=msg["content"]))
                else:
                    formatted_history.append(AIMessage(content=msg["content"]))

            # Chuẩn bị state với đầy đủ ngữ cảnh
            state = {
                "messages": [HumanMessage(content=user_input)],
                "conversation_history": formatted_history,
                "context_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "session_id": st.session_state.session_info["session_id"],
                    "interaction_count": st.session_state.session_info["user_interactions"]
                }
            }

            # Xử lý qua graph
            response_content = None
            with st.spinner("🤔 Đang xử lý..."):
                for step in st.session_state.graph.stream(state):
                    if isinstance(step, dict):
                        current_node = next(iter(step.keys()))
                        logger.info(f"Đang xử lý tại node: {current_node}")

                    response = self._get_last_response(step)
                    if response and response.content.strip():
                        response_content = response.content
                        logger.info(f"Nhận phản hồi từ {current_node}")
                        break

            # Cập nhật ngữ cảnh với tương tác mới
            if response_content:
                st.session_state.session_info["user_interactions"] += 1
                self.update_conversation_context(user_input, response_content)

            return response_content or "Xin lỗi, tôi không thể xử lý yêu cầu này."

        except Exception as e:
            logger.error(f"Lỗi xử lý tin nhắn: {str(e)}")
            return "Xin lỗi, có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại."

    def run(self):
        """Chạy giao diện chat chính với xử lý ngữ cảnh và đa tác tử"""
        st.title("🏦 HDBank AI Assistant")

        # Hiển thị thông tin ngữ cảnh trong sidebar
        with st.sidebar:
            st.title("🏦 HDBank Assistant")
            st.markdown("---")

            # Hiển thị thống kê hội thoại
            st.markdown("### Thống kê cuộc hội thoại")
            context = st.session_state.conversation_context
            st.write(f"Số lượng tương tác: {context['interaction_count']}")
            if context['last_product_query']:
                st.write("Chủ đề gần đây nhất về sản phẩm:")
                st.write(context['last_product_query'])

            # Nút xóa lịch sử
            if st.button("🗑️ Xóa lịch sử chat"):
                st.session_state.messages = [{
                    "role": "assistant",
                    "content": self.welcome_message
                }]
                st.session_state.conversation_context = {
                    "current_topic": None,
                    "last_product_query": None,
                    "interaction_count": 0,
                    "context_history": []
                }
                st.rerun()

            st.markdown("---")
            st.markdown("### Thông tin")
            st.markdown("AI Assistant phiên bản 1.0")
            st.markdown("© 2024 Hackathon HDBank. All rights reserved.")

        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Xử lý input từ người dùng
        if user_input := st.chat_input("Nhập câu hỏi của bạn..."):
            # Cập nhật UI với tin nhắn người dùng
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Xử lý và hiển thị phản hồi
            with st.chat_message("assistant"):
                response = self.process_message(user_input)

                if response:
                    # Hiển thị phản hồi với animation
                    message_placeholder = st.empty()
                    full_response = self.stream_response(response, message_placeholder)

                    # Cập nhật lịch sử
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })
                else:
                    st.error("Xin lỗi, tôi không thể xử lý yêu cầu này.")

    def stream_response(self, response: str, placeholder):
        """
        Hiển thị phản hồi với hiệu ứng đánh máy tự nhiên.

        Args:
            response: Nội dung phản hồi cần hiển thị
            placeholder: Streamlit placeholder để cập nhật nội dung
        """
        try:
            # Khởi tạo buffer cho nội dung hoàn chỉnh
            full_response = []

            # Tách response thành các dòng
            lines = response.strip().split('\n')

            for line in lines:
                # Tách dòng thành các từ
                words = line.split()
                line_buffer = []

                for word in words:
                    # Thêm từ vào buffer của dòng hiện tại
                    line_buffer.append(word)

                    # Hiển thị dòng hiện tại và các dòng trước đó
                    current_response = '\n'.join(full_response + [' '.join(line_buffer) + " ▌"])
                    placeholder.markdown(current_response)
                    time.sleep(0.05)

                # Khi hoàn thành một dòng, thêm vào buffer tổng
                full_response.append(' '.join(line_buffer))

            # Hiển thị phản hồi hoàn chỉnh cuối cùng
            final_response = '\n'.join(full_response)
            placeholder.markdown(final_response)
            return final_response

        except Exception as e:
            logger.error(f"Lỗi hiển thị response: {str(e)}")
            placeholder.markdown(response)
            return response

        except Exception as e:
            logger.error(f"Lỗi hiển thị response: {str(e)}")
            placeholder.markdown(response)
            return response


    def _get_last_response(self, step: Dict[str, Any]) -> Optional[AIMessage]:
        """
        Trích xuất phản hồi cuối cùng từ bước xử lý của graph.

        Args:
            step: Bước xử lý hiện tại từ graph

        Returns:
            Optional[AIMessage]: Message cuối cùng từ agent hoặc None
        """
        try:
            if isinstance(step, dict):
                for value in step.values():
                    if isinstance(value, dict) and "messages" in value:
                        messages = value["messages"]
                        if messages and isinstance(messages[-1], AIMessage):
                            return messages[-1]
            return None

        except Exception as e:
            logger.error(f"Lỗi khi lấy response: {str(e)}")
            return None


    def _handle_special_commands(self, user_input: str) -> bool:
        """
        Xử lý các lệnh đặc biệt từ người dùng.

        Args:
            user_input: Câu lệnh từ người dùng

        Returns:
            bool: True nếu là lệnh đặc biệt và đã được xử lý
        """
        try:
            # Xử lý lệnh clear
            if user_input.lower() in ['/clear', 'clear', 'xóa']:
                self._clear_chat_history()
                return True

            # Xử lý lệnh help
            if user_input.lower() in ['/help', 'help', 'trợ giúp']:
                self._show_help()
                return True

            # Xử lý lệnh export
            if user_input.lower().startswith('/export'):
                self._export_chat_history()
                return True

            return False

        except Exception as e:
            logger.error(f"Lỗi xử lý lệnh đặc biệt: {str(e)}")
            return False


    def _clear_chat_history(self):
        """Xóa lịch sử chat và khởi tạo lại trạng thái"""
        try:
            st.session_state.messages = [{
                "role": "assistant",
                "content": self.welcome_message
            }]
            st.session_state.conversation_context = {
                "current_topic": None,
                "last_product_query": None,
                "interaction_count": 0,
                "context_history": []
            }
            st.rerun()

        except Exception as e:
            logger.error(f"Lỗi khi xóa lịch sử: {str(e)}")
            st.error("Không thể xóa lịch sử chat. Vui lòng thử lại.")


    def _show_help(self):
        """Hiển thị hướng dẫn sử dụng chatbot"""
        help_message = """
            🔍 Hướng dẫn sử dụng HDBank AI Assistant:
    
            Các lệnh đặc biệt:
            • /clear: Xóa lịch sử chat
            • /help: Hiển thị hướng dẫn này
            • /export: Xuất lịch sử chat
    
            Các loại câu hỏi:
            • Thông tin sản phẩm (thẻ, vay, tiết kiệm...)
            • Lãi suất và biểu phí
            • Thủ tục, quy trình giao dịch
            • Ưu đãi và khuyến mãi
            • Các câu hỏi chung về HDBank
    
            Tips sử dụng hiệu quả:
            • Đặt câu hỏi rõ ràng, cụ thể
            • Cung cấp đầy đủ thông tin cần thiết
            • Kiên nhẫn chờ hệ thống xử lý
            """
        st.info(help_message)


    def _export_chat_history(self):
        """Xuất lịch sử chat ra file"""
        try:
            # Tạo nội dung xuất
            export_content = []
            for msg in st.session_state.messages:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                export_content.append(f"{timestamp} - {msg['role']}: {msg['content']}")

            # Tạo file
            filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(export_content))

            # Thông báo thành công
            st.success(f"Đã xuất lịch sử chat vào file {filename}")

        except Exception as e:
            logger.error(f"Lỗi khi xuất lịch sử: {str(e)}")
            st.error("Không thể xuất lịch sử chat. Vui lòng thử lại.")
def main():
    """
    Hàm main khởi chạy ứng dụng với xử lý lỗi toàn diện
    và logging chi tiết.
    """
    try:
        # Thiết lập logging chi tiết cho môi trường production
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('app.log'),
                logging.handlers.RotatingFileHandler(
                    'app_rotating.log',
                    maxBytes=10485760,  # 10MB
                    backupCount=5
                )
            ]
        )

        # Khởi tạo và chạy giao diện chat
        chat_interface = HDBANKChatInterface()

        # Thêm thông tin phiên làm việc
        st.session_state.session_info = {
            "start_time": datetime.now(),
            "session_id": str(hash(datetime.now())),
            "user_interactions": 0
        }

        # Chạy giao diện chính
        chat_interface.run()

    except Exception as e:
        logger.error(f"Lỗi khởi động ứng dụng: {str(e)}", exc_info=True)
        st.error("Có lỗi xảy ra khi khởi động ứng dụng. Vui lòng tải lại trang.")

    finally:
        # Đảm bảo log phiên làm việc được lưu
        if hasattr(st.session_state, 'session_info'):
            logger.info(f"Kết thúc phiên làm việc {st.session_state.session_info['session_id']}")





if __name__ == "__main__":
    main()