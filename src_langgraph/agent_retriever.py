from typing import Annotated
from langchain_core.tools import tool
from vector_database import VectorDB
from langchain.retrievers import EnsembleRetriever  # Kết hợp nhiều retriever
from langchain_community.retrievers import BM25Retriever  # Retriever dựa trên BM25
from langchain_core.documents import Document

@tool
def get_retriever(
    input_text: Annotated[str, "Văn bản truy vấn chứa các từ khóa hoặc câu hỏi để tìm thông tin sản phẩm liên quan."],
    collection_name: Annotated[str, "Tên của tập dữ liệu để tìm kiếm, mặc định là 'product_personal'."] = 'product_personal'
):
    """
    Tạo và trả về một retriever kết hợp từ Qdrant và BM25.

    Đầu vào:
    - collection_name (str): Tên của collection trong Qdrant mà bạn muốn truy xuất dữ liệu.

    Đầu ra:
    - EnsembleRetriever: Một đối tượng retriever kết hợp, sử dụng cả Qdrant và BM25 để tìm kiếm tài liệu.
    """
    collection_name = 'product_personal'
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
            weights=[0.7, 0.3]  # Trọng số cho mỗi retriever
        )
        documents = ensemble_retriever.invoke(input_text)
        if documents:
            doc = documents[0]  # Lấy sản phẩm liên quan nhất
            return [{"content": doc.page_content, "metadata": doc.metadata}]
        else:
            return []  # Trả về danh sách rỗng nếu không có tài liệu nào
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

def test_get_retriever():
    # Sample input
    input_text = "HD Bank Vietjet Platinum?"
    collection_name = 'product_personal'

    # Call get_retriever function
    retriever_output = get_retriever(input_text, collection_name)
    print(retriever_output)
    # Print output
    if retriever_output:
        for doc in retriever_output:
            print("Content:", doc["content"])
            print("Metadata:", doc["metadata"])
    else:
        print("No documents found.")

if __name__ == "__main__":
    test_get_retriever()