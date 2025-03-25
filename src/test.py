from agent_retrieve import get_retriever
from langchain.tools import Tool

# Hàm tạo tool từ retriever với khả năng trả về metadata
def create_retriever_tool_with_metadata(retriever, name: str, description: str) -> Tool:
    """
    Tạo một tool từ retriever với khả năng trả về metadata.

    Đầu vào:
    - retriever: Đối tượng retriever để truy xuất tài liệu.
    - name (str): Tên của tool.
    - description (str): Mô tả về tool.

    Đầu ra:
    - Tool: Đối tượng tool với khả năng trả về nội dung và metadata.
    """
    def retrieve_function(input_text: str):
        # Gọi retriever để lấy tài liệu
        doc = retriever.invoke(input_text)
        # Trả về nội dung và metadata
        result = doc[0].page_content + doc[0].metadata
        return result.replace(r"\n","")

    return Tool(
        name=name,
        description=description,
        func=retrieve_function,
    )

# Lấy retriever
retriever = get_retriever()

# Tạo tool từ retriever với khả năng trả về metadata
tool = create_retriever_tool_with_metadata(
    retriever,
    'retrieve_product',
    "Truy xuất các sản phẩm liên quan"
)

# Gọi tool và in kết quả
result = tool.func("HDBank Vietjet Platinum")  # Gọi hàm retrieve_function
for item in result:
    print("Nội dung:", item["content"])  # In ra nội dung
    print("Metadata:", item["metadata"])  # In ra metadata