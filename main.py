# Import thư viện Gemini AI
import google.generativeai as genai

# Import thư viện làm việc với hệ điều hành và biến môi trường
import os
from dotenv import load_dotenv
from pprint import pformat

# Import FastAPI và Pydantic
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Import pyodbc để kết nối SQL Server
import pyodbc

# Tải biến môi trường
load_dotenv()

# Cấu hình API key cho Gemini
genai.configure(api_key=os.getenv("API_KEY"))

# Khởi tạo mô hình Gemini
model = genai.GenerativeModel("gemini-1.5-flash")

# ===== KẾT NỐI SQL SERVER =====
def get_products():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=14.225.253.29,1433;"
        "DATABASE=DearFab;"
        "UID=sa;"
        "PWD=winnertech123@;"
        "TrustServerCertificate=Yes;"
        "Encrypt=Yes;"
        "MultipleActiveResultSets=True;"
    )
    products = []
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP (1000) [Id], [Name], [Description], [Image], 
                       [IsNew], [IsActive], [CreateAt], [UpdateAt], [DeleteAt]
                FROM [DearFab].[dbo].[Product]
            """)
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                products.append(dict(zip(columns, row)))
    except Exception as e:
        print("Database error:", e)
    return products

# Định nghĩa schema dữ liệu cho request
class ChatRequest(BaseModel):
    prompt: str

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="DearFab Chatbot API",
    description="Chatbot DearFab",
    version="1.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint GET /
@app.get("/")
async def read_root():
    return {"message": "Welcome to DearFab Chatbot! Visit /docs to see API documentation and try /chat with POST."}

# Endpoint POST /chat
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Lấy danh sách sản phẩm từ DB
        products = get_products()
        product_context = pformat(products, width=120)

        prompt = f"""
        Bạn là chatbot thân thiện của DearFab - website bán tranh vải tái chế.
        Dưới đây là danh sách các sản phẩm tranh vải của DearFab:

        {product_context}
        Khi nào khách hàng hỏi đến sản phẩm thì hãy
        Hãy sử dụng thông tin này để tư vấn sản phẩm, kiểm tra hàng còn hay không, giới thiệu sản phẩm nổi bật, mới, hoặc theo kích cỡ nếu người dùng hỏi.
        Khi muốn in đậm, bạn dùng dấu ** như **này**. Khi xuống dòng thì dùng dấu \\n\\n.
        Khi người dùng hỏi về cách liên hệ, hãy bảo họ nhắn qua Facebook fanpage DearFab: https://www.facebook.com/share/1D6g3LzNCj/?mibextid=wwXIfr hoặc Zalo: 0877888036

        Câu hỏi: {request.prompt}
        """
        response = model.generate_content(prompt)
        return {"message": response.text}
    except Exception as e:
        return {"message": f"Lỗi: {str(e)}"}

# Chạy ứng dụng
if __name__ == "__main__":
    import uvicorn
    import os
    port = 8000
    try:
        port_str = os.environ.get("PORT", "8000").strip()
        print(f"Raw PORT value: {port_str}")
        if port_str.endswith("."):
            port_str = port_str[:-1]
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port {port} is out of valid range (1-65535)")
    except (ValueError, TypeError) as e:
        print(f"Invalid port value: {e}. Falling back to port 8000.")
        port = 8000
    print(f"Starting uvicorn on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
