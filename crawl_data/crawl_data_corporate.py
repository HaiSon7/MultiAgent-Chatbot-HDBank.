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

    # Lấy thẻ div có class 'desc-wrap' và tất cả các thẻ <p> bên trong
    desc_wrap_paragraphs = driver.find_elements(By.CSS_SELECTOR, 'div.desc-wrap p')
    desc_wrap_group = []
    for p in desc_wrap_paragraphs:
        text = p.text.strip()
        if text:  # Kiểm tra nếu đoạn văn không rỗng
            desc_wrap_group.append(text)

    # Thêm nhóm từ desc_wrap vào danh sách lớn nếu có
    if desc_wrap_group:
        all_text_groups.append(desc_wrap_group)

    # Lấy tất cả các thẻ wrap-item trong .wrapper-insurance .wrapper-container
    wrap_items = driver.find_elements(By.CSS_SELECTOR, '.wrapper-insurance .wrapper-container .wrap-item')
    
    for item in wrap_items:
        item_group = []  # Tạo một nhóm cho từng wrap-item
        paragraphs = item.find_elements(By.TAG_NAME, 'p')
        for p in paragraphs:
            text = p.text.strip()
            if text:  # Kiểm tra nếu đoạn văn không rỗng
                item_group.append(text)

        # Thêm nhóm từ wrap-item vào danh sách lớn nếu có
        if item_group:
            all_text_groups.append(item_group)

    # Đóng trình duyệt
    driver.quit()

    # Hiển thị kết quả
    for index, group in enumerate(all_text_groups):
        print(f"Text Group {index + 1}: {group}")

    return all_text_groups


def get_links_from_level_3(url):
    # Khởi tạo trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # Mở trang web
    driver.get(url)

    # Tìm tất cả các thẻ <li> trong <ul> có id 'accordian' và class 'level-3'
    li_elements = driver.find_elements(By.CSS_SELECTOR, '#accordian li ul.level-3 li')

    # Tạo danh sách để lưu trữ các link
    links = []
    for li in li_elements:
        # Tìm thẻ <a> trong thẻ <li>
        a_tag = li.find_element(By.TAG_NAME, 'a')
        link = a_tag.get_attribute('href')  # Lấy thuộc tính href
        if link:  # Kiểm tra nếu link không rỗng
            links.append(link)

    # Đóng trình duyệt
    driver.quit()

    return links

# URL của trang cần crawl
url = 'https://hdbank.com.vn/vi/corporate/'
urls = get_links_from_level_3(url)

# URL của trang cần crawl
url_fail = []
for url in urls:
    print(url)
    # URL của trang cần crawl
    result = crawl_hdbank(url)
    if len(result) <=2:
        url_fail.append(url)
        continue
    
    title = " ".join(result[0])
    description = " ".join(result[1])
    utilities = " ".join(result[2])
    features = " ".join(result[4]) if len(result) > 4 else ""
    profile = " ".join(result[5]) if len(result) > 5 else ""

    customer_segment = " ".join(result[3]) if len(result) > 3 else ""
    related_promotion = '''
    Thực hiện và đồng hành theo chủ trương của Ngân hàng Nhà nước trong việc tích cực hỗ trợ doanh nghiệp, hỗ trợ thúc đẩy tăng trưởng kinh tế Thành phố Hồ Chí Minh thông qua các chương trình hỗ trợ lãi suất, gói vay ưu đãi hay cơ cấu nhóm nợ. HDBank đã triển khai chương trình:
Tên chương trình: “KẾT NỐI NGÂN HÀNG – DOANH NGHIỆP NĂM 2024”
Phạm vi áp dụng: địa bàn TP Hồ Chí Minh.
Thời gian áp dụng: đến hết ngày 31/12/2024 hoặc khi đã đạt đến hạn mức của Chương trình.
Hạn mức của chương trình: 1.000 tỷ đồng.
Loại tiền cho vay: VND
Mục đích sử dụng vốn vay: phục vụ các phương án, dự án sản xuất kinh doanh hàng xuất nhập khẩu; sản xuất kinh doanh của doanh nghiệp.
Kỳ hạn: ngắn hạn hoặc trung dài hạn
Lãi suất áp dụng (*):
+ Ngắn hạn: tối thiểu 6,90%/năm
+ Trung dài hạn: 8,90%/năm
(*) Điều kiện và điều khoản theo quy định của HDBank.
Thông qua chương trình kết nối ngân hàng - doanh nghiệp, HDBank không những tạo điều kiện hỗ trợ vốn và nâng cao khả năng tiếp cận tín dụng cho doanh nghiệp mà còn góp phần bảo đảm an sinh xã hội, cải thiện đời sống và tạo công ăn việc làm cho người dân trên địa bàn Thành phố Hồ Chí Minh.
HDBank hy vọng Quý Doanh nghiệp sẽ liên hệ ngay điểm giao dịch gần nhất của HDBank để chúng tôi có cơ hội cung cấp các giải pháp tài chính toàn diện và ưu đãi nhất cùng với nhiều tiện ích vượt trội đến Quý khách hàng.
HDBank tin tưởng sẽ là lựa chọn ưu tiên hàng đầu trong việc đồng hành phát triển của Quý Doanh nghiệp.
Kính chúc Quý Doanh nghiệp luôn thành công và nhận nhiều ưu đãi khi giao dịch với HDBank.
    '''
    
    details = {
        'utilities': utilities,
        'features': features,
        'profile': profile,
        'customer segment': customer_segment
    }

    p = Product(url, title, description, details, related_promotion)
    print(p)

    filename = 'C:\Python\AI\Hackathon_HDBank_2024\crawl_data\product_corporate.json'
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
