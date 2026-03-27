from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re
from typing import Annotated

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = Field(None, gt=0)
    is_subscribed: Optional[bool] = False

class Product(BaseModel):
    product_id: int
    name: str
    category: str
    price: float

class CommonHeaders(BaseModel):
    # Используем Alias, чтобы Pydantic понимал заголовки с дефисами
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")

    @field_validator("accept_language")
    @classmethod
    def validate_accept_language(cls, v: str):
        # Регулярка теперь разрешает буквы, цифры и спецсимволы заголовка
        pattern = r"^[a-zA-Z0-9\-_,;=.* ]+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid Accept-Language format")
        return v

# from pydantic import BaseModel, EmailStr, Field, ConfigDict

# class User(BaseModel):
#     name: str
#     id: int

# class Feedback(BaseModel):
#     name: str
#     message: str