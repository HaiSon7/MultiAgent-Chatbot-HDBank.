from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore,RetrievalMode
from qdrant_client.http.models import Distance, VectorParams
from config import QDRANT_URL,API_KEY
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import json

class VectorDB():
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=API_KEY,
            timeout=60
        )
        self.embeddings = HuggingFaceEmbeddings(model_name="keepitreal/vietnamese-sbert")
        

    def upload_data(self,file_path:str,collection_name:str):
        with open(file_path, 'r',encoding='utf-8') as file:
            data = json.load(file)

        documents = [
        Document(
            page_content=(doc.get('title', '') +'. '+ doc.get('description', '')),
            metadata={
                'url': doc.get('url') or '',
                'title': doc.get('title') or '',
                'description': doc.get('description') or '',
                'details': doc.get('details'),
                'related_promotion':doc.get('related_promotion')
            }
        )
        for doc in data
        
    ]
        ids = [doc.get('id') for doc in data]
        collections = self.qdrant_client.get_collections()
        if collection_name not in collections:
            self.qdrant_client.create_collection(collection_name=collection_name,
                                                 vectors_config=VectorParams(size=768, distance=Distance.COSINE))
            print('Create Collection Done')
        vectorstore = QdrantVectorStore(client=self.qdrant_client,
                                             collection_name=collection_name,
                                             embedding=self.embeddings)

        vectorstore.add_documents(documents=documents,ids = ids)
        print('Upload Done')

    def connet_to_qdrant(self,collection_name : str) ->QdrantVectorStore:
        vectorstore = QdrantVectorStore(client=self.qdrant_client,
                                             collection_name=collection_name,
                                             embedding=self.embeddings
                                       )
        if not vectorstore:
            return 0
        return vectorstore


if __name__ == "__main__":
    vectordb = VectorDB()
    vectordb.upload_data(r'C:\Python\AI\Hackathon_HDBank_2024\crawl_data\product.json','product_personal')
    vectordb.upload_data(r'C:\Python\AI\Hackathon_HDBank_2024\crawl_data\product_corporate.json','product_corporate')