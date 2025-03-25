from langchain.tools.retriever import create_retriever_tool
from langchain.tools import Tool
from langchain.agents import AgentExecutor,create_tool_calling_agent
from langchain_ollama import ChatOllama
from vector_database import VectorDB
from langchain.retrievers import EnsembleRetriever  # Kết hợp nhiều retriever
from langchain_community.retrievers import BM25Retriever  # Retriever dựa trên BM25
from langchain_core.documents import Document  # Lớp Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def get_retriever(collection_name:str = 'product_personal')-> EnsembleRetriever:
    """
    Tạo và trả về một retriever kết hợp từ Qdrant và BM25.

    Đầu vào:
    - collection_name (str): Tên của collection trong Qdrant mà bạn muốn truy xuất dữ liệu.

    Đầu ra:
    - EnsembleRetriever: Một đối tượng retriever kết hợp, sử dụng cả Qdrant và BM25 để tìm kiếm tài liệu.
    """
    vector_db = VectorDB()  # Khởi tạo đối tượng VectorDB để kết nối với Qdrant

    try:
        # Kết nối đến Qdrant và lấy vectorstore
        vectorstore = vector_db.connet_to_qdrant(collection_name)
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 1}  # Số lượng kết quả tương tự cần tìm
        )

        # Tạo danh sách tài liệu từ Qdrant
        documents = [
            Document(page_content=doc.page_content, metadata=doc.metadata)
            for doc in vectorstore.similarity_search("", k=10)  # Tìm kiếm 20 tài liệu tương tự
        ]

        # Kiểm tra xem có tài liệu nào được tìm thấy không
        if not documents:
            raise ValueError(f"Không tìm thấy documents trong collection '{collection_name}'")

        # Tạo BM25 retriever từ danh sách tài liệu
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = 1  # Số lượng kết quả tối đa từ BM25

        # Kết hợp retriever từ Qdrant và BM25
        ensemble_retriever = EnsembleRetriever(
            retrievers=[retriever, bm25_retriever],
            weights=[0.8, 0.2]  # Trọng số cho mỗi retriever
        )
        return ensemble_retriever  # Trả về retriever kết hợp
    except Exception as e:
        print(f"Lỗi khi khởi tạo retriever: {str(e)}")
        # Trả về retriever với document mặc định nếu có lỗi
        default_doc = [
            Document(
                page_content="Có lỗi xảy ra khi kết nối database. Vui lòng thử lại sau.",
                metadata={"source": "error"}
            )
        ]
        default_bm25_retriever = BM25Retriever.from_documents(default_doc)
        return default_bm25_retriever  # Trả về BM25 retriever với tài liệu mặc định


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
        documents = retriever.invoke(input_text)
        if documents:
            doc = documents[0]  # Lấy sản phẩm liên quan nhất
            return [{"content": doc.page_content, "metadata": doc.metadata}]
        else:
            return []  # Trả về danh sách rỗng nếu không có tài liệu nào

    return Tool(
        name=name,
        description=description,
        func=retrieve_function,
    )


def get_agent_retrieve(retriever) -> AgentExecutor:

    # Khởi tạo mô hình ngôn ngữ
    llm = ChatOllama(model="llama3.2:3b",
                     temperature=0.2,
                     streaming=False
                     )
    tool = create_retriever_tool_with_metadata(
    retriever,
    'retrieve_product',
    "tìm kiếm sản phẩm liên quan"
)
    # Danh sách các công cụ
    tools = [tool]

    # Cấu hình hệ thống
    system = '''Bạn là Assistant AI , nhân viên tư vấn sản phẩm của Ngân hàng HD Bank.
                Xác định nội dung yêu cầu của user và sử dụng công cụ truy xuất.
                Sau đó tổng hợp lại thông tin người dùng yêu cầu để trả lời người dùng.
                '''
    # Tạo prompt cho agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Tạo agent với công cụ và prompt đã cấu hình
    agent_ = create_tool_calling_agent(llm = llm ,tools= tools,prompt=prompt)

    # Trả về AgentExecutor
    return AgentExecutor(agent=agent_, tools=tools, verbose=True)


retrive = get_retriever()


