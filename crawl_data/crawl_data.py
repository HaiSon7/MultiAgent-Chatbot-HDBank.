from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import json
from product import Product

def crawl_with_selenium(url):
    # Khởi tạo trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # Mở trang web
    driver.get(url)

    # Tạo danh sách lớn để lưu trữ các nhóm văn bản
    all_text_groups = []

    # Lấy thẻ <h1> với class 'title title_small title_small-black'
    title_h1_elements = driver.find_elements(By.CSS_SELECTOR, 'h1.title.title_small.title_small-black')
    title_group = []
    for h1 in title_h1_elements:
        h1_text = h1.text.strip()
        if h1_text:  # Kiểm tra nếu thẻ <h1> không rỗng
            title_group.append(h1_text)

    # Thêm nhóm từ title vào danh sách lớn nếu có
    if title_group:
        all_text_groups.append(title_group)

    # Tìm tất cả các thẻ .wrap-item trong cấu trúc cụ thể
    wrap_items = driver.find_elements(By.CSS_SELECTOR, '.wrapper-insurance .wrapper-container .wrap-item')

    # Lọc và nhóm các thẻ <p> trong từng thẻ .wrap-item
    for item in wrap_items:
        current_group = []

        # Lấy tất cả các thẻ <p> trong thẻ wrap-item
        paragraphs = item.find_elements(By.TAG_NAME, 'p')
        for p in paragraphs:
            text = p.text.strip()
            if text:  # Kiểm tra nếu đoạn văn không rỗng
                current_group.append(text)

        # Thêm nhóm vào danh sách lớn nếu có
        if current_group:
            all_text_groups.append(current_group)

    # Lấy tất cả các thẻ <p> trong .wrapper-insurance .desc-wrap
    desc_wrap_paragraphs = driver.find_elements(By.CSS_SELECTOR, '.wrapper-insurance .desc-wrap p')
    desc_wrap_group = []
    for p in desc_wrap_paragraphs:
        text = p.text.strip()
        if text:  # Kiểm tra nếu đoạn văn không rỗng
            desc_wrap_group.append(text)

    # Thêm nhóm từ desc-wrap vào danh sách lớn
    if desc_wrap_group:
        all_text_groups.append(desc_wrap_group)

    # In ra từng nhóm văn bản
    for index, group in enumerate(all_text_groups):
        print(f"Text Group {index + 1}:\n{group}\n")  # In ra từng nhóm dưới dạng mảng

    
    # Đóng trình duyệt
    driver.quit()

    return all_text_groups# URL của trang cần crawl
url = 'https://hdbank.com.vn/vi/personal/product/detail/san-pham-vay/vay-bat-dong-san/vay-bat-dong-san'
result = crawl_with_selenium(url)


title = " ".join(result[0])


description = " ".join(result[5])
utilities = " ".join(result[1])

features = " ".join(result[2])
profile = " ".join(result[3])

customer_segment= " ".join(result[4])
related_promotion = ''
related_promotion = '''
Thời gian triển khai: Từ 09/05/2023
 Phạm vi áp dụng: Tất cả ĐVKD trên toàn hệ thống
 Đối tượng khách hàng: Khách hàng cá nhân có độ tuổi từ 25 đến 45 tuổi tại thời điểm xét duyệt khoản vay; đang đi làm tại các cơ quan/công ty/tổ chức có thu nhập từ lương và các nguồn thu nhập khác (nếu có) được chuyển khoản qua ngân hàng và thỏa quy định sản phẩm hiện hành của HDBank.
 Chính sách ưu đãi:
- Hạn mức gói tín dụng: 10.000 Tỷ đồng
- Sản phẩm vay: Cho vay mua nhà (không bao gồm xây, sửa nhà) đối với Khách hàng cá nhân.
- Số tiền vay: tối thiểu 500 triệu đồng.
- Thời hạn cho vay: Trên 5 năm.
- Lãi suất cho vay: ưu đãi 8,2%/năm trong 03 tháng đầu.
- Lãi suất cho vay: ưu đãi 9,2%/năm trong 06 tháng đầu.
Để biết thêm chi tiết về chương trình, vui lòng liên hệ với HDBank gần nhất hoặc Tổng đài CSKH 1900 6060 (24/7) hoặc Email: info@hdbank.com.vn để được hỗ trợ.'''

details = {
    'utilities': utilities,
    'features' : features,
    'profile' : profile,
    'customer segment' : customer_segment
}

p = Product(url, title, description, details,related_promotion)
print(p)

filename = 'product.json'
try:
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
except FileNotFoundError:
    # Nếu file không tồn tại, khởi tạo một mảng rỗng
    data = []

# Thêm dữ liệu mới vào mảng
data.append(p.to_dict())

# Ghi lại toàn bộ dữ liệu vào file JSON (ghi đè)
with open(filename, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print("Thêm dữ liệu vào mảng JSON thành công.")
