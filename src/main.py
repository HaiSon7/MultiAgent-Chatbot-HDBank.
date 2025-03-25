import streamlit as st  # Thư viện tạo giao diện web
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from agent_retrieve import get_agent_retrieve, get_retriever
from agent_llm import get_agent_llm

gemma2_9b = "gemma2:latest"
gemma2_2b = "gemma2:2b"
gemma2_2btool="cow/gemma2_tools:2b"
vistral = "ontocord/vistral:latest"
collections = ("product_personal", "product_corporate")


# Cấu hình trang web cơ bản
def setup_page():
    st.set_page_config(
        page_title="AI Assistant HD Bank",  # Tiêu đề tab trình duyệt
        page_icon="💬",  # Icon tab
        layout="wide"  # Giao diện rộng
    )


# Hàm thiết lập sidebar
def setup_sidebar():
    st.sidebar.title("Bạn muốn tìm hiểu về các sản phẩm, dịch vụ của Cá nhân hay Doanh nghiệp ?")
    product_type = st.sidebar.selectbox("", ["--------------------------", "Cá nhân",
                                             "Doanh Nghiệp"])  # Không có lựa chọn mặc định
    if product_type == "Cá nhân":
        collection_name = collections[0]
    else:
        collection_name = collections[1]
    return collection_name, product_type


def get_relevant_product(chat_history, agent_executor):
    prompt = chat_history[-1].get("content")
    response = agent_executor.invoke(
        {
            "input": prompt,
            "chat_history": chat_history
        }
    )
    return response["output"]


# Hàm xử lý đầu vào của người dùng
def handle_user_input(msgs, agent_llm):
    if prompt := st.chat_input('Tôi có thể giúp gì cho bạn '):
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        msgs.add_user_message(prompt)
        # Lấy lịch sử chat
        chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.messages
        ]
        with st.chat_message("assistant"):
            # st_callback = StreamlitCallbackHandler(st.container())
            output = ""
            placeholder = st.empty()
            for w in agent_llm.stream(chat_history):
                output += w.content
                placeholder.markdown(f"<p>{output} ▐ </p>", unsafe_allow_html=True)
            placeholder.markdown(f"<p>{output}</p>", unsafe_allow_html=True)
            # retriever = get_retriever(collection_name)
            # agent_executor = get_agent(retriever)
            # Gọi AI xử lý

            # print(response)
            # # Lưu và hiển thị câu trả lời
            # output = response.content
            st.session_state.messages.append({"role": "assistant", "content": output})
            msgs.add_ai_message(output)


# Hàm chính để chạy ứng dụng
def main():
    # Hiển thị lựa chọn của người dùng
    if product_type != "--------------------------":
        st.write(f"Bạn đã chọn: **{product_type}**")
        st.write("**Rất vui vì bạn đã quan tâm đến sản phẩm của HD Bank. Tôi có thể giúp gì cho bạn?**")
        # Hiển thị lịch sử cuộc trò chuyện
        for msg in st.session_state.messages:
            role = "assistant" if msg["role"] == "assistant" else "user"
            st.chat_message(role).write(msg["content"])
        agent_llm = get_agent_llm(gemma2_2btool, 0.5)

        handle_user_input(msgs, agent_llm)  # Gọi hàm xử lý đầu vào


    else:
        st.write("Vui lòng chọn loại sản phẩm, dịch vụ.")


# Chạy ứng dụng
if __name__ == "__main__":
    setup_page()  # Cấu hình trang
    st.title("💬 AI Assistant HD Bank")  # Tiêu đề ứng dụng
    collection_name, product_type = setup_sidebar()  # Thiết lập sidebar và lấy lựa chọn của người dùng
    msgs = StreamlitChatMessageHistory(key="langchain_messages")

    # Khởi tạo lịch sử cuộc trò chuyện
    if "messages" not in st.session_state:
        st.session_state.messages = []
    main()
