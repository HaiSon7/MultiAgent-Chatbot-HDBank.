from typing import Annotated, List, Dict, Any
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from vector_database import VectorDB
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re


class AdvancedRetriever:
    """
    Retriever nâng cao với khả năng xác thực kết quả đa tầng.
    """

    def __init__(self, llm_shared):
        self.llm_shared = llm_shared
        # Khởi tạo cross-encoder để reranking và validation
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.confidence_threshold = 0.8
        self.vector_db = VectorDB()

    def search_and_validate(self, query: str, collection_name: str = 'product_personal') -> List[Dict[str, Any]]:
        """
        Tìm kiếm và xác thực kết quả qua nhiều bước.
        """
        try:
            # Bước 1: Initial Search
            vectorstore = self.vector_db.connet_to_qdrant(collection_name)
            initial_results = vectorstore.similarity_search(query, k=5)

            if not initial_results:
                return self._format_no_result()

            # Bước 2: Content Validation
            validated_results = self._validate_content(query, initial_results)
            if not validated_results:
                return self._format_no_result()

            # Bước 3: Semantic Reranking
            reranked_results = self._semantic_reranking(query, validated_results)
            if not reranked_results:
                return self._format_no_result()

            # Bước 4: Final Validation
            final_result = self._final_validation(query, reranked_results[0])
            if not final_result:
                return self._format_no_result()

            return [final_result]

        except Exception as e:
            print(f"Lỗi trong quá trình tìm kiếm: {str(e)}")
            return self._format_no_result()

    def _validate_content(self, query: str, documents: List[Document]) -> List[Document]:
        """
        Xác thực nội dung của các kết quả tìm kiếm.
        """
        validated_docs = []

        for doc in documents:
            # Kiểm tra độ dài tối thiểu
            if len(doc.page_content.strip()) < 10:
                continue

            # Kiểm tra tính hợp lệ của metadata
            if not self._validate_metadata(doc.metadata):
                continue

            # Kiểm tra semantic similarity
            similarity_score = self._calculate_similarity(query, doc.page_content)
            if similarity_score < self.confidence_threshold:
                continue

            validated_docs.append(doc)

        return validated_docs

    def _semantic_reranking(self, query: str, documents: List[Document]) -> List[Document]:
        """
        Xếp hạng lại kết quả dựa trên độ tương đồng ngữ nghĩa.
        """
        if not documents:
            return []

        # Chuẩn bị pairs cho cross-encoder
        pairs = [(query, doc.page_content) for doc in documents]

        # Tính toán điểm số
        scores = self.cross_encoder.predict(pairs)

        # Sắp xếp documents theo điểm số
        ranked_pairs = list(zip(documents, scores))
        ranked_pairs.sort(key=lambda x: x[1], reverse=True)

        # Lọc kết quả có điểm số cao hơn ngưỡng
        filtered_docs = [doc for doc, score in ranked_pairs if score >= self.confidence_threshold]

        return filtered_docs

    def _final_validation(self, query: str, document: Document) -> Dict[str, Any]:
        """
        Kiểm tra cuối cùng kết quả tốt nhất.
        """
        # Tạo prompt kiểm tra
        validation_prompt = f"""Xác minh xem thông tin sau có thực sự trả lời câu hỏi hay không.

        Câu hỏi: {query}

        Thông tin: {document.page_content}

        Phân tích:
        1. Thông tin có trả lời trực tiếp câu hỏi không?
        2. Thông tin có đầy đủ và chính xác không?
        3. Có phải là thông tin chung chung không liên quan không?

        Chỉ trả về: VALID hoặc INVALID"""

        # Kiểm tra với LLM
        response = self.llm_shared.invoke(validation_prompt)
        is_valid = "VALID" in response.content.upper()

        if is_valid:
            return {
                "content": document.page_content,
                "metadata": document.metadata,
                "confidence": "HIGH"
            }
        return None

    def _validate_metadata(self, metadata: Dict) -> bool:
        """
        Kiểm tra tính hợp lệ của metadata.
        """
        required_fields = ['title', 'description']

        # Kiểm tra các trường bắt buộc
        if not all(field in metadata for field in required_fields):
            return False

        # Kiểm tra nội dung các trường
        if not all(metadata[field].strip() for field in required_fields):
            return False

        return True

    def _calculate_similarity(self, query: str, content: str) -> float:
        """
        Tính toán độ tương đồng ngữ nghĩa.
        """
        pair = (query, content)
        score = float(self.cross_encoder.predict([pair])[0])
        return score

    def _format_no_result(self) -> List[Dict[str, Any]]:
        """
        Trả về kết quả NO RESULT theo định dạng chuẩn.
        """
        return [{"content": "NO RESULT", "metadata": {}, "confidence": "LOW"}]


@tool

def get_retriever(
        input_text: Annotated[
            str, "Văn bản truy vấn chứa các từ khóa hoặc câu hỏi để tìm thông tin sản phẩm liên quan."]
):
    """
    Tìm kiếm thông tin sản phẩm với khả năng chuyển tiếp sang searcher khi không tìm thấy kết quả.
    """
    llm_shared = ChatOllama(model="llama3.2:3b", temperature=0.3)
    try:
        # Khởi tạo các thành phần cần thiết
        vector_db = VectorDB()
        vectorstore = vector_db.connet_to_qdrant('product_personal')
        documents = []

        # Bước 1: Tìm kiếm trong vector database
        try:
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 3}  # Tăng số lượng kết quả để có nhiều lựa chọn hơn
            )
            results = retriever.invoke(input_text)
            if results:
                documents.extend(results)
        except Exception as e:
            print(f"Lỗi khi tìm kiếm vector: {str(e)}")

        # Bước 2: Tìm kiếm với BM25 nếu có đủ documents
        if documents:
            try:
                bm25_docs = [
                    Document(page_content=doc.page_content, metadata=doc.metadata)
                    for doc in documents
                ]
                bm25_retriever = BM25Retriever.from_documents(bm25_docs)
                bm25_retriever.k = 3
                bm25_results = bm25_retriever.get_relevant_documents(input_text)
                documents.extend(bm25_results)
            except Exception as e:
                print(f"Lỗi khi tìm kiếm BM25: {str(e)}")

        # Bước 3: Xác thực và lọc kết quả
        validated_results = []
        if documents:
            # Cross-encoder để xác thực độ liên quan
            cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

            for doc in documents:
                # Tính điểm tương đồng
                score = cross_encoder.predict([(input_text, doc.page_content)])
                if score > 0.7:  # Ngưỡng điểm cao để đảm bảo chất lượng
                    validated_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score)
                    })

        # Bước 4: Kiểm tra kết quả và quyết định chuyển tiếp
        if validated_results:
            # Sắp xếp theo điểm số và lấy kết quả tốt nhất
            validated_results.sort(key=lambda x: x["score"], reverse=True)
            best_result = validated_results[0]

            # Xác nhận lại với LLM
            verification_prompt = f"""Verify if this result truly answers the query:
            Query: {input_text}
            Result: {best_result['content']}
            Return only VALID or INVALID"""

            verification = llm_shared.invoke(verification_prompt).content.strip()

            if "VALID" in verification.upper():
                return [best_result]

        # Nếu không tìm thấy kết quả hợp lệ, trả về NO RESULT để chuyển sang searcher
        print("Không tìm thấy kết quả phù hợp, chuyển sang searcher")
        return [{"content": "NO RESULT", "metadata": {}}]

    except Exception as e:
        print(f"Lỗi trong retriever: {str(e)}")
        return [{"content": "NO RESULT", "metadata": {}}]