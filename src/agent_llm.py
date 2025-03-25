from langchain_ollama import ChatOllama

# template = """Bạn là Asisstant AI tư vấn sản phẩm của ngân hàng HD Bank.
#                 Hãy trả lời ngắn gọn và chi tiết.
#                 Đảm bảo trả lời dựa trên các thông tin được cung cấp.
#     """
def get_agent_llm(model,temperature,streaming = True):
    # Cấu hình Ollama LLM với mô hình
    llm = ChatOllama(model=model,
                    temperature = temperature,
                    streaming = streaming
                     )

    return llm
