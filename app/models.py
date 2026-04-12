from pydantic import BaseModel, EmailStr, Field

class UserBasic(BaseModel):
    username: str
    user_info: str

class NestedUser(BaseModel):
    name: str
    age: int


class UserResponseNested(BaseModel):
    message: str
    user: NestedUser


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int | None = Field(default=None, gt=0)
    is_subscribed: bool | None = False


class CommonHeaders(BaseModel):
    user_agent: str = Field(alias="User-Agent")
    accept_language: str = Field(alias="Accept-Language")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    username: str
    role: str = "user"


class UserAuth(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegisterDB(BaseModel):
    username: str
    password: str


class TodoCreate(BaseModel):
    title: str
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str
    description: str | None = None
    completed: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
