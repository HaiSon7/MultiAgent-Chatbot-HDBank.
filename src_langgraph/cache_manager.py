from typing import Dict, Set, Tuple, List
import json
from datetime import datetime, timedelta
import os

class ProductCache:
    """
    Quản lý cache thông tin sản phẩm với các tính năng:
    - Lưu trữ thông tin và từ khóa
    - Tìm kiếm thông minh dựa trên từ khóa
    - Tự động lưu và tải cache từ file
    - Xử lý thời gian hết hạn cache
    """
    def __init__(self, cache_file: str = "product_cache.json", expire_days: int = 7):
        self.cache_file = cache_file
        self.expire_days = expire_days
        self.cache: Dict[str, dict] = {}
        self.keywords: Dict[str, Set[str]] = {}
        self.banking_keywords = {
            'thẻ', 'tín dụng', 'vay', 'lãi suất', 'tài khoản', 
            'tiết kiệm', 'ngân hàng', 'hdbank', 'phí', 'dịch vụ',
            'visa', 'mastercard', 'atm', 'internet banking', 'mobile banking',
            'chuyển khoản', 'thanh toán', 'số dư', 'giao dịch'
        }
        self._load_cache()

    def add_to_cache(self, query: str, info: str) -> None:
        """Thêm thông tin mới vào cache với timestamp"""
        query = query.lower().strip()
        keywords = set(self._extract_keywords(query) + self._extract_keywords(info))
        
        self.cache[query] = {
            'info': info,
            'timestamp': datetime.now().isoformat(),
            'keywords': list(keywords)
        }
        self.keywords[query] = keywords
        
        print(f"Cache: Đã thêm thông tin mới với {len(keywords)} từ khóa")
        self._save_cache()

    def find_matching_info(self, query: str) -> Tuple[bool, str]:
        """Tìm thông tin phù hợp trong cache với scoring system"""
        self._clean_expired_entries()
        query_keywords = set(self._extract_keywords(query))
        
        best_match = None
        highest_score = 0
        
        for cached_query, data in self.cache.items():
            cached_keywords = set(data['keywords'])
            score = self._calculate_match_score(query_keywords, cached_keywords)
            
            if score > highest_score:
                highest_score = score
                best_match = cached_query

        if best_match and highest_score >= 0.5:  # Ngưỡng điểm 50%
            print(f"Cache: Tìm thấy kết quả với độ phù hợp {highest_score:.2%}")
            return True, self.cache[best_match]['info']
        
        print("Cache: Không tìm thấy thông tin phù hợp")
        return False, ""

    def _calculate_match_score(self, query_keywords: Set[str], cached_keywords: Set[str]) -> float:
        """Tính điểm phù hợp dựa trên tỷ lệ từ khóa trùng khớp và trọng số"""
        if not query_keywords or not cached_keywords:
            return 0
        
        matching_keywords = query_keywords & cached_keywords
        
        # Tính điểm dựa trên tỷ lệ từ khóa trùng khớp
        base_score = len(matching_keywords) / max(len(query_keywords), len(cached_keywords))
        
        # Thêm trọng số cho các từ khóa quan trọng
        important_matches = sum(1 for k in matching_keywords if k in self.banking_keywords)
        weight = 1 + (important_matches * 0.2)  # Tăng 20% cho mỗi từ khóa quan trọng
        
        return base_score * weight

    def _extract_keywords(self, text: str) -> List[str]:
        """Trích xuất từ khóa từ văn bản với xử lý ngôn ngữ tiếng Việt"""
        text = text.lower().strip()
        
        # Tách từ và cụm từ
        words = text.split()
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        
        # Kết hợp tất cả các n-gram
        all_potential_keywords = words + bigrams + trigrams
        
        # Lọc từ khóa dựa trên từ điển ngành ngân hàng
        keywords = {
            kw for kw in all_potential_keywords 
            if any(bank_kw in kw for bank_kw in self.banking_keywords)
        }
        
        return list(keywords)

    def _clean_expired_entries(self) -> None:
        """Xóa các entry đã hết hạn"""
        current_time = datetime.now()
        expired_queries = []
        
        for query, data in self.cache.items():
            cache_time = datetime.fromisoformat(data['timestamp'])
            if current_time - cache_time > timedelta(days=self.expire_days):
                expired_queries.append(query)
        
        for query in expired_queries:
            del self.cache[query]
            del self.keywords[query]
            
        if expired_queries:
            print(f"Cache: Đã xóa {len(expired_queries)} entries hết hạn")
            self._save_cache()

    def _save_cache(self) -> None:
        """Lưu cache vào file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Cache: Lỗi khi lưu cache: {e}")

    def _load_cache(self) -> None:
        """Tải cache từ file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                    
                # Khôi phục keywords từ cache
                for query, data in self.cache.items():
                    self.keywords[query] = set(data['keywords'])
                    
                print(f"Cache: Đã tải {len(self.cache)} entries từ file")
        except Exception as e:
            print(f"Cache: Lỗi khi tải cache: {e}")
