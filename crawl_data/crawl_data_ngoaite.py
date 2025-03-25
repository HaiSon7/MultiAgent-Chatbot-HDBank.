from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from product import Product
import json

def crawl_hdbank(url):
    # Khởi tạo trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # Mở trang web
    driver.get(url)

    # Tạo danh sách lớn để lưu trữ các nhóm văn bản
    all_text_groups = []

    # Lấy thẻ <h1> với class 'title title_small title_small-black'
    h1_elements = driver.find_elements(By.CSS_SELECTOR, 'h1.title.title_small.title_small-black')
    h1_group = []
    for h1 in h1_elements:
        h1_text = h1.text.strip()
        if h1_text:  # Kiểm tra nếu thẻ <h1> không rỗng
            h1_group.append(h1_text)

    # Thêm nhóm từ h1 vào danh sách lớn nếu có
    if h1_group:
        all_text_groups.append(h1_group)

    # Lấy tất cả các thẻ <p> trong div có class 'desc-wrap'
    desc_wrap_paragraphs = driver.find_elements(By.CSS_SELECTOR, 'div.desc-wrap p')
    desc_wrap_group = []
    for p in desc_wrap_paragraphs:
        text = p.text.strip()
        if text:  # Kiểm tra nếu đoạn văn không rỗng
            desc_wrap_group.append(text)

    # Thêm nhóm từ desc_wrap vào danh sách lớn nếu có
    if desc_wrap_group:
        all_text_groups.append(desc_wrap_group)

    # Lấy tất cả các thẻ loan-list_item trong div có class 'row-loan-list'
    loan_list_items = driver.find_elements(By.CSS_SELECTOR, 'div.row-loan-list div.wrap-item_content')
    
    for item in loan_list_items:
        loan_item_group = []  # Tạo một nhóm cho từng loan item
        paragraphs = item.find_elements(By.TAG_NAME, 'p')
        for p in paragraphs:
            text = p.text.strip()
            if text:  # Kiểm tra nếu đoạn văn không rỗng
                loan_item_group.append(text)

        # Thêm nhóm từ loan item vào danh sách lớn nếu có
        if loan_item_group:
            all_text_groups.append(loan_item_group)

    # Đóng trình duyệt
    driver.quit()
    
    return all_text_groups

# Danh sách các URL cần crawl
urls = [
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-tham-vieng-du-lich',
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-thanh-toan-le-phi',
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-dinh-cu',
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-thua-ke',
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-du-hoc',
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-chua-benh',
    'https://hdbank.com.vn/vi/personal/product/detail/ngoai-te/chuyen-tien-quoc-te/chuyen-theo-muc-dich-tro-cap'
]

for url in urls:
    # URL của trang cần crawl
    result = crawl_hdbank(url)
    print(result)
    
    title = " ".join(result[0])
    description = " ".join(result[1])
    utilities = " ".join(result[2])
    features = " ".join(result[3]) if len(result) > 3 else ""
    profile = " ".join(result[4]) if len(result) > 4 else ""

    customer_segment = " Tất cả mọi người "
    related_promotion = '''
    Chương trình "Giao Dịch Ngoại Tệ Cùng HDBank - Mời Bạn Mới Tiền Tấn Tới", áp dụng dành cho cộng tác viên khi giới thiệu khách hàng cá nhân mua ngoại tệ thành công tại các Chi nhánh / Phòng giao dịch HDBank trên toàn quốc trong năm 2024.
    KHÔNG GIỚI HẠN SỐ TIỀN THƯỞNG khi CTV giới thiệu thành công khách hàng mua ngoại tệ.
    Đối tượng tham gia: Tất cả cộng tác viên cá nhân.
    Thời gian triển khai: Từ ngày 01/02/2024 đến khi có chương trình khác thay thế.
    Điều kiện giới thiệu khách hàng cá nhân mua ngoại tệ hợp lệ:
    1. Mỗi giao dịch tối thiểu 10.000 USD hoặc ngoại tệ khác quy đổi tương đương.
    2. Giao dịch ngoại tệ hợp lệ: USD, EUR, CAD, AUD, GBP, CHF, SGD, NZD. (Không áp dụng đối với JPY, THB, HKD).
    3. Khách hàng được giới thiệu phải đến Chi nhánh / Phòng giao dịch HDBank để tiến hành giao dịch mua ngoại tệ.
    4. Ngày phát sinh giao dịch mua ngoại tệ của khách hàng được giới thiệu tại CN / PGD phải sau hoặc bằng ngày CTV nhập thông tin giới thiệu khách hàng.
    (Chương trình có kèm điều kiện áp dụng)
    Hướng dẫn đăng ký CTV trên ứng dụng HDBank Mobile banking & Giới thiệu khách hàng:
    Bước 1: Đăng ký trở thành Cộng tác viên trên ứng dụng HDBank Mobile Banking của HDBank.
    Bước 2: Giới thiệu khách hàng cá nhân đến Chi nhánh / Phòng giao dịch HDBank mua ngoại tệ.
    Bước 3: Nhập thông tin giới thiệu khách hàng cá nhân trên ứng dụng HDBank Mobile Banking.
    Để tìm hiểu thêm thông tin chương trình hoặc tư vấn dịch vụ, Quý khách hàng vui lòng liên hệ qua Email:kdngoaihoi@hdbank.com.vn hoặc đến các điểm giao dịch HDBank trên toàn quốc.
    '''
    
    details = {
        'utilities': utilities,
        'features': features,
        'profile': profile,
        'customer segment': customer_segment
    }

    p = Product(url, title, description, details, related_promotion)
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

