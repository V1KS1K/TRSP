from pydantic import BaseModel, EmailStr, Field, ConfigDict

class User(BaseModel):
    name: str
    id: int

class Feedback(BaseModel):
    name: str
    message: str