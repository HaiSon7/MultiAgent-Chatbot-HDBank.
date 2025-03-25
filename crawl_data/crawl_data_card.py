from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import json
from product import Product
def crawl_hdbank(url):
    # Khởi tạo trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # Mở trang web
    driver.get(url)

    # Tạo danh sách lớn để lưu trữ các nhóm văn bản
    all_text_groups = []

    # Tìm thẻ <h1> với class '.card-detail .title-sec'
    h1_elements = driver.find_elements(By.CSS_SELECTOR, '.card-detail .title-sec')
    title_group = []
    for h1 in h1_elements:
        h1_text = h1.text.strip()
        if h1_text:  # Kiểm tra nếu thẻ <h1> không rỗng
            title_group.append(h1_text)

    # Thêm nhóm từ title vào danh sách lớn nếu có
    if title_group:
        all_text_groups.append(title_group)

    # Tìm thẻ <h1> trong div có class 'wrapper-detail_content'
    h1_elements = driver.find_elements(By.CSS_SELECTOR, 'div.wrapper-detail_content h1')
    for h1 in h1_elements:
        h1_text = h1.text.strip()
        if h1_text:  # Kiểm tra nếu thẻ <h1> không rỗng
            title_group.append(h1_text)

    # Thêm nhóm từ title vào danh sách lớn nếu có
    if title_group:
        all_text_groups.append(title_group)

    # Tìm tất cả các thẻ <p> trong div có class 'wrapper-detail_content'
    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'div.wrapper-detail_content p')
    paragraph_group = []
    for p in paragraphs:
        text = p.text.strip()
        if text:  # Kiểm tra nếu đoạn văn không rỗng
            paragraph_group.append(text)

    # Thêm nhóm từ paragraphs vào danh sách lớn nếu có
    if paragraph_group:
        all_text_groups.append(paragraph_group)

    # Tìm tất cả các thẻ <h2> và <li> trong div có class 'benefit-and-feature_desc'
    col_divs = driver.find_elements(By.CSS_SELECTOR, 'div.col-12.col-md-12.col-lg-6.col-xl-6')

    # Lặp qua từng thẻ div
    for col_div in col_divs:
        # Tìm thẻ <h2> trong thẻ div hiện tại
        h2_elements = col_div.find_elements(By.TAG_NAME, 'h2')
        h2_group = []
        
        for h2 in h2_elements:
            h2_text = h2.text.strip()
            if h2_text:  # Kiểm tra nếu thẻ <h2> không rỗng
                h2_group.append(h2_text)

        # Tìm tất cả các thẻ <li> trong thẻ div hiện tại
        li_elements = col_div.find_elements(By.TAG_NAME, 'li')
        li_group = []
        
        for li in li_elements:
            li_text = li.text.strip()
            if li_text:  # Kiểm tra nếu thẻ <li> không rỗng
                li_group.append(li_text)

        # Nếu có cả h2 và li, thêm vào danh sách lớn
        if h2_group or li_group:
            combined_group = h2_group + li_group  # Kết hợp h2 và li vào một mảng con
            all_text_groups.append(combined_group)
    
    # Đóng trình duyệt
    driver.quit()
    return all_text_groups
# URL của trang cần crawl
url = 'https://hdbank.com.vn/vi/personal/product/detail/the/the-tra-truoc/hdbank-dai-ichi'
result  = crawl_hdbank(url)



title = " ".join(result[0])


description = " ".join(result[2])
utilities = " ".join(result[3])

features = " ".join(result[4])
profile = " Trên 18 tuổi"

customer_segment= " Tất cả mọi người "
related_promotion = ''
related_promotion = '''
MUA 1 ĐƠN ÁP 2 MÃ TRÊN SENDO KHI TRẢ GÓP QUA MUADEE
Khi mua sắm trên ứng dụng Sendo và chọn thanh toán qua Thẻ trả góp Muadee by HDBank, bạn có thể áp dụng 2 mã ưu đãi trên cùng 1 đơn hàng. 
Giảm 30.000vnđ 
Đơn hàng từ 500.000vnđ 
Mỗi khách hàng 01/lượt/tháng  
Áp mã ưu đãi tại trang thanh toán của Sendo 
Miễn phí vận chuyển  
Giảm 30.000vnđ cho đơn hàng từ 299.000vnđ 
Mỗi khách hàng 02/lượt/tháng  
Áp mã ưu đãi tại trang thanh toán của Sendo  
 Thời gian: Chương trình ưu đãi kéo dài đến hết tháng 08/2024 
 Điều kiện áp dụng  
- Đối mã Miễn phí vận chuyển không áp dụng cho sản phẩm thuộc Điện tử - Công nghệ - Thú cưng. 
- Được áp dụng đồng thời với một số chương trình khuyến mãi khác từ Sendo.  
- Giá trị ưu đãi không được quy đổi thành tiền mặt. 
 Giới thiệu chung  
Với thẻ trả góp Muadee by HDBank, không chỉ đáp ứng được nhu cầu, sở thích của các bạn trẻ; mà còn cung cấp một giải pháp thanh toán “Mua trước trả sau" khi đăng ký online trong 5 phút, duyệt ngay hạn mức đến 30 triệu không cần chứng minh thu nhập và đặc biệt:  
Trả góp trong 4 tháng   
Không lãi suất, không phí ẩn, không phí thường niên 
An toàn, bảo mật bởi HDBank
(*) Nếu chưa có tài khoản thẻ trả góp Muadee, bạn có thể đăng ký ngay: 
'''
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