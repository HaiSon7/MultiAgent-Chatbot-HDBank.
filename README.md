# HDBank Multi-Agent Chatbot System

## 🌟 Overview

The HDBank Multi-Agent Chatbot is an advanced AI assistant designed to provide accurate and contextually relevant information about HDBank's products and services. This system leverages a multi-agent architecture to process queries through specialized components, ensuring high accuracy and comprehensive responses.

## 🏗️ System Architecture

The system employs a sophisticated multi-agent architecture where different specialized components work together:

```
User Query → Supervisor → Product Cache → Retriever → Searcher → Assistant → Response
```

![Architecture Flowchart]()

### Key Components:

1. **Supervisor**: Routes queries based on category (product-related or general)
2. **Product Cache**: Checks for existing information in the cache system
3. **Retriever**: Searches the vector database for relevant product information
4. **Searcher**: Performs online searches for up-to-date information if needed
5. **Assistant**: Generates user-friendly responses based on gathered information

## 🤖 Agent Descriptions

### Supervisor Agent
- **Purpose**: Query classification and routing
- **Implementation**: `build_graph.py:ContextAnalyzer`
- **Functionality**: Analyzes user queries to determine if they're about banking products or general inquiries, then routes to the appropriate processing path

### Product Cache
- **Purpose**: Fast retrieval of frequently requested information
- **Implementation**: `cache_manager.py:ProductCache`
- **Functionality**: 
  - Stores previous product information with keyword extraction
  - Performs smart matching with scoring system
  - Manages cache expiry and persistence

### Retriever Agent
- **Purpose**: Access internal product knowledge base
- **Implementation**: `agent_retriever.py:get_retriever`
- **Functionality**:
  - Combines vector similarity search (Qdrant) and keyword search (BM25)
  - Optimizes for semantic and lexical matching
  - Returns the most relevant product information

### Searcher Agent
- **Purpose**: Find up-to-date information online
- **Implementation**: `agent_tavily_search.py:tavily_search`
- **Functionality**:
  - Uses Tavily API for targeted web searches
  - Focuses on HDBank domain (hdbank.com.vn)
  - Formats and returns relevant search results

### Assistant Agent
- **Purpose**: Generate natural, user-friendly responses
- **Implementation**: `build_graph.py:GraphBuilder.assistant_agent`
- **Functionality**:
  - Formats information from other agents
  - Maintains conversation context
  - Presents information in a helpful, concise manner

## 📊 Vector Database

The system uses Qdrant vector database with HuggingFace embeddings specifically tuned for Vietnamese language:

- **Implementation**: `vector_database.py`
- **Model**: "keepitreal/vietnamese-sbert"
- **Features**:
  - Document storage with metadata
  - Semantic search capabilities
  - Cosine similarity distance metrics

## 🔄 Data Flow Process

1. User submits a query
2. Supervisor classifies the query type
3. For product queries:
   - System checks the product cache first
   - If not found, searches vector database
   - If still not found, performs an online search
   - Caches new information for future use
4. For general queries, routes directly to the assistant
5. Assistant generates a natural language response

## 🚀 Installation and Setup

### Prerequisites

- Python 3.8+
- Qdrant server (local or cloud)
- Ollama for local LLM execution
- Required Python packages

### Environment Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/hdbank-chatbot.git
cd hdbank-chatbot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure your environment variables in a `.env` file:
```
QDRANT_URL=your_qdrant_url
API_KEY=your_qdrant_api_key
TAVILY_API_KEY=your_tavily_api_key
```

4. Prepare your product data in JSON format (see example structure in `vector_database.py:upload_data`)

5. Upload your data to the vector database:
```bash
python vector_database.py
```

## 💻 Running the Application

Start the Streamlit application:

```bash
streamlit run streamlit_app.py
```

The application will be available at http://localhost:8501 by default.

## 🔧 Configuration

You can modify the behavior of the chatbot by adjusting parameters in `build_graph.py`:

```python
MODELS = {
    'llm_shared': "llama3.2:3b",  # Model for retriever and searcher
    'llm_assistant': "gemma2:2b",  # Model for assistant
    'llm_supervisor': "llama3.2:3b",  # Model for context analysis
    'temperature_default': 0.3,
    'temperature_retriever': 0.2,
    'temperature_supervisor': 0.2
}
```

## 📝 Usage Examples

### Example 1: Product Query
```
User: "Tôi muốn biết về lãi suất thẻ tín dụng HDBank Visa Platinum"
Assistant: [Provides information about HDBank Visa Platinum credit card interest rates]
```

### Example 2: General Query
```
User: "Giờ làm việc của HDBank vào cuối tuần là gì?"
Assistant: [Provides information about HDBank weekend working hours]
```

## 🔍 Troubleshooting

- **Connection Issues**: Ensure your Qdrant and Tavily API credentials are correctly configured
- **Slow Responses**: Check if the cache system is working properly
- **Incorrect Answers**: You may need to update your vector database with more current information

## 🔮 Future Enhancements

1. Implement user authentication and personalized responses
2. Add support for document upload and analysis
3. Integrate with HDBank's internal systems for real-time data
4. Improve Vietnamese language understanding with specialized models
5. Implement A/B testing for different response strategies

## 📄 License

This project is proprietary and confidential. Unauthorized copying, use, distribution, or modification is strictly prohibited.

## 👥 Contributors

- [Your Name]
- [Team Members]

---

*Developed for HDBank Hackathon 2024*
