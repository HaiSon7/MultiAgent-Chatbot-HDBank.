from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Đường dẫn tới thư mục chứa mô hình
model_directory = r"C:\Python\AI\Hackathon_HDBank_2024\models"

# Tải tokenizer và model từ thư mục chứa cấu hình và mô hình
tokenizer = AutoTokenizer.from_pretrained(model_directory)
model = AutoModelForCausalLM.from_pretrained(model_directory)

# Kiểm tra xem có GPU không, nếu có thì sử dụng GPU, nếu không thì dùng CPU
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


def generate_response(prompt):
    # Mã hóa câu hỏi đầu vào
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    # Sinh câu trả lời
    with torch.no_grad():
        outputs = model.generate(inputs["input_ids"], max_length=512, temperature=0.7, num_return_sequences=1)

    # Giải mã câu trả lời
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


# Ví dụ sử dụng mô hình
prompt = "Hi there! How can I help you today?"
response = generate_response(prompt)

print("Response:", response)
