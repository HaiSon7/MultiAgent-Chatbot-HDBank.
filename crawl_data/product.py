import uuid
import json
from collections import defaultdict
class Product:
    def __init__(self, url, title, description, details,related_promotion = None):
        self.id = str(uuid.uuid4())
        self.url = url
        self.title = title
        self.description = description
        self.details = {}
        self.related_promotion = related_promotion

        if isinstance(details, dict):
            self.details.update(details)
    
    def to_dict(self):
        """Chuyển đổi đối tượng thành dictionary"""
        return {
            'id' : self.id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'details': self.details,
            'related_promotion' :self.related_promotion 
        }
    
    
    def __str__(self):
        return f"Product(id = {self.id},url={self.url}, title={self.title}, description={self.description}, details={self.details},related_promotion = {self.related_promotion})"

url = 'https://hdbank.com.vn/vi/personal/product/detail/the/the-tin-dung/the-hdbank-priority-visa-signature'
title = " Thẻ HDBank Priority – Tinh Tú Phương Đông "
description = "Hoàn tiền lên đến 9,6 triệu đồng/năm . Chiếc thẻ màu đỏ rượu vang sang trọng, hội tụ hàng loạt đặc quyền hấp dẫn cho khách hàng đặc biệt, mang đến cho khách hàng phong cách sống chuẩn \"sao\" với chuỗi hành trình trải nghiệm hạnh phúc với những điểm chạm thanh toán ưu việt."
utilities = '''
Quà tặng mở thẻ
Miễn phí thường niên năm đầu
Lợi ích
Hoàn tiền 15% cho giao dịch mua sắm hàng hóa với giá trị hoàn tối thiểu 100.000 đồng/ tháng, và  tối đa 300.000 đồng/ tháng.
Tìm hiểu chi tiết mã loại hình mua sắm được hoàn  xem tại đây.
Hoàn tiền 0,5% cho các giao dịch chi tiêu khác như y tế, giáo dục, bảo hiểm... giá trị hoàn tối thiểu 100.000 đồng/ tháng, tối đa 500.000 đồng/ tháng.
Đặc quyền theo quý: Chủ thẻ có tổng giao dịch hằng Quý mỗi 100.000.000 đồng sẽ nhận được một (01) lượt vào phòng chờ sân bay hoặc giảm 1.000.000 đồng (đã bao gồm thuế GTGT) cho một (01) lượt chơi tại sân Golf có liên kết với HDBank. Số lượt được tặng tối đa 4 lượt/năm. Xem chi tiết tại đây.
Bảo hiểm du lịch toàn cầu đến 12 tỷ đồng. Xem chi tiết Quy tắc bảo hiểm và Mẫu giấy chứng nhận bảo hiểm.
Giảm đến 40% chi phí đặt phòng, ăn uống hoặc dịch vụ giải trí tại Pullman Phú Quốc, Aria Đà Nẵng, Royal Hạ Long Hotel,  L'Alya Ninh Van Bay, Almanity Hoi An Resort & Spa, Hệ thống F&B Mylife Group, Miss Thu Restaurant,..
Giảm đến 50% khi chơi Golf tại hệ thống các FCL,sân Cửa Lo Golf, Lang Cô Laguna... 
Chủ thẻ được phục vụ theo hotline VIP 1800 6868 của HDBank.
Trả góp lãi suất 0% tại các đối tác liên kết của HDBank.
'''

features = '''
Giảm giá lên đến 50%
Khi chơi Golf tại câu lạc bộ liên kết của HDBank.
Hoàn tiền 15%
Mua sắm hàng hóa.
Hoàn tiền 0,5%
Cho các giao dịch chi tiêu khác.
Miễn lãi tối đa 55 ngày.
Miễn phí thường niên năm đầu tiên với giá trị đến 1,9 triệu đồng.
Miễn phí thường niên năm đầu tiên dành cho Chủ thẻ phụ.
Hạn mức tín dụng từ 100 triệu đến 10 tỷ đồng.
An toàn bảo mật với chip EMV, công nghệ xác thực thanh toán 3D - Secure.
 
'''
profile = '''

'''
customer_segment= '''
'''
related_promotion = ''
related_promotion1= '''
MỞ RỘNG KẾT NỐI

Hãy giới thiệu người thân/bạn bè trở thành Khách hàng Đặc biệt và nhận thưởng lên đến 1.500.000 đồng vào tài khoản

MUA 1 ĐƠN ÁP 2 MÃ TRÊN SENDO KHI TRẢ GÓP QUA MUADEE

Giảm 30K tặng thêm freeship khi mua sắm trên Sendo và chọn thanh toán bằng Thẻ trả góp Muadee by HDBank

Xem chi tiết : https://hdbank.com.vn/vi/personal/promotion/detail/the/mua-1-don-ap-2-ma-tren-sendo-khi-tra-gop-qua-muadee

GIẢM 150K TẠI HOÀNG HÀ MOBILE VÀ BẠCH LONG MOBILE VỚI THẺ TRẢ GÓP MUADEE

Gấp đôi "sự sung sướng" khi biết tin Bạch Long Mobile và Hoàng Hà Mobile kết hợp cùng Thẻ trả góp Muadee. Lên đời máy cũ mà không "áp lực tài chính" vì được trả góp 4 tháng, không lãi suất và không phí ẩn. 

Xem chi tiết : https://hdbank.com.vn/vi/personal/promotion/detail/the/giam-150k-tai-hoang-ha-mobile-va-bach-long-mobile-voi-the-tra-gop-muadee


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

