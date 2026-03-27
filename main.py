from fastapi import FastAPI, Response, Cookie, HTTPException, Depends, Header, Request
from typing import List, Optional, Annotated  # <--- Добавь Annotated сюда
import models
import uuid
import time
import hmac
import hashlib
import base64
from datetime import datetime

app = FastAPI()

SECRET_KEY = "super-secret-key"

class CookieSigner:
    @staticmethod
    def sign(value: str) -> str:
        signature = hmac.new(SECRET_KEY.encode(), value.encode(), hashlib.sha1).digest()
        encoded_sig = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        return f"{value}.{encoded_sig}"

    @staticmethod
    def unsign(signed_value: str) -> Optional[str]:
        try:
            if "." not in signed_value: return None
            value, sig = signed_value.rsplit(".", 1)
            expected_sig = base64.urlsafe_b64encode(
                hmac.new(SECRET_KEY.encode(), value.encode(), hashlib.sha1).digest()
            ).decode().rstrip('=')
            if hmac.compare_digest(sig, expected_sig):
                return value
        except Exception:
            return None
        return None

#3.2
sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99},
]

#3.1
@app.post("/create_user", tags=["3.1"])
def create_user(user: models.UserCreate):
    return user

#3.2
@app.get("/products/search", tags=["3.2"])
def search_products(keyword: str, category: Optional[str] = None, limit: int = 10):
    results = [p for p in sample_products if keyword.lower() in p["name"].lower()]
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    return results[:limit]

@app.get("/product/{product_id}", tags=["3.2"])
def get_product(product_id: int):
    product = next((p for p in sample_products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

#5.1-5.3
@app.post("/login", tags=["5.1-5.3"])
def login(response: Response):
    user_id = str(uuid.uuid4())
    current_time = int(time.time())
    
    unsigned_value = f"{user_id}.{current_time}"
    signed_token = CookieSigner.sign(unsigned_value)
    
    response.set_cookie(
        key="session_token",
        value=signed_token,
        httponly=True,
        max_age=300 
    )
    return {"message": "Logged in successfully", "user_id": user_id}

@app.get("/profile", tags=["5.1-5.3"])
def get_profile(response: Response, session_token: Optional[str] = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail={"message": "Unauthorized"})
    
    unsigned_value = CookieSigner.unsign(session_token)
    if not unsigned_value:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})
    
    try:
        user_id, timestamp_str = unsigned_value.split(".")
        last_activity = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=401, detail={"message": "Invalid session format"})

    current_time = int(time.time())
    elapsed = current_time - last_activity

    if elapsed > 300:
        raise HTTPException(status_code=401, detail={"message": "Session expired"})
    
    if 180 <= elapsed < 300:
        new_unsigned = f"{user_id}.{current_time}"
        new_token = CookieSigner.sign(new_unsigned)
        response.set_cookie(key="session_token", value=new_token, httponly=True, max_age=300)

    return {
        "user_id": user_id,
        "last_activity": datetime.fromtimestamp(last_activity).isoformat(),
        "status": "Active"
    }

#5.4-5.5
@app.get("/headers", tags=["5.4-5.5"])
def get_headers(
    user_agent: Annotated[str, Header()], 
    accept_language: Annotated[str, Header()]
):
    # Мы создаем модель вручную из полученных заголовков для валидации
    headers_model = models.CommonHeaders(**{"User-Agent": user_agent, "Accept-Language": accept_language})
    return {
        "User-Agent": headers_model.user_agent,
        "Accept-Language": headers_model.accept_language
    }

@app.get("/info", tags=["5.5"])
def get_info(
    response: Response,
    user_agent: Annotated[str, Header()], 
    accept_language: Annotated[str, Header()]
):
    # Валидируем через модель
    headers_model = models.CommonHeaders(**{"User-Agent": user_agent, "Accept-Language": accept_language})
    
    server_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    response.headers["X-Server-Time"] = server_time
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers_model.user_agent,
            "Accept-Language": headers_model.accept_language
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# @app.get("/", tags=["1.2"])
# async def read_index():
#     return FileResponse("index.html")

# #--------------------------------------------------------------------
# num1 = 5
# num2 = 10

# @app.post("/calculate", tags=["1.3*"])
# def calculate1():
#     return num1 + num2
# #----------------------------------------------------------------------

# user_data = models.User(name="Ваше Имя и Фамилия", id=1)

# @app.get("/user", tags=["1.4"])
# def get_user_info():
#     return user_data

# #----------------------------------------------------------------------

# feedbacks_list = []

# @app.post("/feedback", tags=["2.1"])
# def create_feedback(feedback: models.Feedback):
#     feedbacks_list.append(feedback.model_dump())
#     return {"message": f"Feedback received. Thank you, {feedback.name}."}

# #-------------------------------------------------------------------------


# #------------------------------------------------------------------------2
# data = {
#     "Email" : "abc@mail.ru",
#     "name" : "Masha",
#     "age" : 12,
#     "gender": "male"
# }

# class Users(BaseModel):
#     Email: EmailStr
#     name: str | None = Field(max_length=10)

#     # mCfg = ConfigDict(extra="forbid") #запрет на данные по умолчанию


# class UsersAge(Users):
#     age: int = Field(ge=0, le=110)

# users = []

# @app.post("/users")
# def add_users(user: Users):
#     users.append(user)
#     return {"ok": True}

# @app.get("/users")
# def get_users() -> list[Users]: #пример как должны вернуться данные
#     return users


# if __name__ == "__main__":
#     uvicorn.app("main.app")

# #-------------------------------------------------------------------------1
# books = [
#     {
#         "id": 1,
#         "title": "Live or Genshin",
#         "autor": "Victoria",
#     },

#     {
#         "id": 2,
#         "title": "Alive",
#         "autor": "Victor",
#     }
# ]


# @app.get('/books', tags=["BOOK"], summary="All book")
# def read_books():
#     return books


# @app.get("/books/{id}", tags=["BOOK"], summary="One Book")
# def get_id_book(id: int):
#     for book in books:
#         if book['id'] == id:
#             return book
#     raise HTTPException(status_code=404, detail="book not founded")


# class New_Book(BaseModel):
#     title: str
#     autor: str


# @app.post("/books", tags=["BOOK"], summary="Create books")
# def create_book(new_book: New_Book):
#     books.append({
#         "id": len(books)+1,
#         "title": new_book.title,
#         "autor": new_book.autor,
#     })
#     return {"succses": True, "message": "Book was created"}

# if __name__ == "__main__":
#     uvicorn.app("main.app")
#--------------------------------------------------------------------------------------

