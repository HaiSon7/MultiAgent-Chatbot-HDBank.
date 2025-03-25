from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import tool
import os

# Cấu hình Tavily API key
os.environ["TAVILY_API_KEY"] = "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"
@tool
def tavily_search(query):
    """Tìm kiếm thông tin mới nhất về sản phẩm, dịch vụ, và ưu đãi của HD Bank."""
    search = TavilySearchResults(
        max_results=5,
        include_answer=False,
        include_images=True,
        search_depth="advanced",
    )

    try:
        # Thêm từ khóa HD Bank vào query
        enhanced_query = f"site:hdbank.com.vn {query}"
        results = search.invoke({
            "query":query,
            "include_answer":False}
            )
        print(results)
        
        # Format kết quả
        if not results:
            return "NO RESULT"
            
        return results
        
    except Exception as e:
        print(f"Error in Tavily search: {e}")
        return "NO RESULT"

if __name__ == "__main__":
    search = TavilySearchResults()
    enhanced_query = "DV Thu tiền có quản lý thông tin HDBank"
    results = search.invoke({
        "query":enhanced_query,
        "include_answer":False}
        )