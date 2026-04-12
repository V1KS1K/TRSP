import re
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Annotated, List

import jwt
from fastapi import Cookie, Depends, FastAPI, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from itsdangerous import BadSignature, Signer
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import load_config
from app.database import get_db_connection, init_db
from app.logger import logger
from app.models import (
    CommonHeaders,
    LoginRequest,
    NestedUser,
    TodoCreate,
    TodoResponse,
    TodoUpdate,
    Token,
    UserAuth,
    UserBasic,
    UserCreate,
    UserInDB,
    UserRegisterDB,
    UserResponseNested,
)


config = load_config()

# Создаем таблицы в БД
init_db()

app = FastAPI(
    title="Professional API Portfolio",
    description="Комплексный API: JWT, RBAC, Rate Limiting, SQLite DB",
    version="4.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

signer = Signer(config.secret_key)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_basic = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/jwt")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


fake_users_db = [{"username": "vasya", "user_info": "любит колбасу"}]
sample_products = [{"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99}]
auth_db: dict[str, UserInDB] = {}

auth_db["admin_master"] = UserInDB(username="admin_master", role="admin", hashed_password=pwd_context.hash("admin123"))


def auth_docs(credentials: HTTPBasicCredentials = Depends(security_basic)):
    if config.mode.upper() == "PROD":
        raise HTTPException(status_code=404, detail="Not Found")
    correct_user = secrets.compare_digest(credentials.username, config.docs_user)
    correct_password = secrets.compare_digest(credentials.password, config.docs_password)
    if not (correct_user and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(username: str = Depends(auth_docs)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Secure API Docs")


@app.get("/openapi.json", include_in_schema=False)
async def get_custom_openapi(username: str = Depends(auth_docs)):
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.get("/", tags=["1. Главная"])
async def root():
    logger.info("Пользователь запросил главную страницу")
    return {"message": "API Works!", "docs": "/docs"}


@app.get("/users/", tags=["2. Базовый CRUD"])
async def get_all_users():
    return fake_users_db


@app.post("/users/add", response_model=UserBasic, tags=["2. Базовый CRUD"])
async def add_user_basic(user: UserBasic):
    fake_users_db.append({"username": user.username, "user_info": user.user_info})
    return user


@app.get("/users/{username}", tags=["2. Базовый CRUD"])
async def get_user_by_name(username: str):
    for user in fake_users_db:
        if user["username"] == username:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/users/{username}", tags=["2. Базовый CRUD"])
async def delete_user(username: str):
    global fake_users_db
    initial_len = len(fake_users_db)
    fake_users_db = [u for u in fake_users_db if u["username"] != username]
    if len(fake_users_db) < initial_len:
        return {"message": f"User {username} deleted"}
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/register/form", tags=["3. Формы и Файлы"])
async def register_user_form(username: Annotated[str, Form(...)], password: Annotated[str, Form(...)]):
    return {"username": username, "password_length": len(password)}


@app.post("/uploadfile/", tags=["3. Формы и Файлы"])
async def create_upload_file(file: UploadFile):
    content = await file.read()
    return {"filename": file.filename, "size": len(content)}


@app.post("/multiple-files/", tags=["3. Формы и Файлы"])
async def upload_multiple_files(files: List[UploadFile]):
    return {"filenames": [file.filename for file in files]}


@app.post("/users/nested", response_model=UserResponseNested, tags=["3. Формы и Файлы"])
async def create_nested_user(user: NestedUser):
    return {"message": "Успешно!", "user": user}


@app.post("/create_user_validated", response_model=UserCreate, tags=["4. Валидация и Поиск"])
async def create_user_validated(user: UserCreate):
    return user


@app.get("/products/search", tags=["4. Валидация и Поиск"])
async def search_products(keyword: Annotated[str, Query()]):
    return [p for p in sample_products if keyword.lower() in p["name"].lower()]


def extract_headers(
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
    accept_language: Annotated[str | None, Header(alias="Accept-Language")] = None,
) -> CommonHeaders:
    if not user_agent or not accept_language:
        raise HTTPException(status_code=400, detail="Missing headers")
    if not re.match(r"^[a-zA-Z0-9\-\,\;\=\.\s]+$", accept_language):
        raise HTTPException(status_code=400, detail="Invalid Accept-Language format")
    return CommonHeaders(**{"User-Agent": user_agent, "Accept-Language": accept_language})


@app.get("/headers", tags=["5. HTTP-Заголовки"])
async def get_headers(headers: Annotated[CommonHeaders, Depends(extract_headers)]):
    return headers.model_dump(by_alias=True)


@app.get("/info", tags=["5. HTTP-Заголовки"])
async def get_info(response: Response, headers: Annotated[CommonHeaders, Depends(extract_headers)]):
    response.headers["X-Server-Time"] = datetime.now().isoformat()
    return {"message": "Успешно", "headers": headers.model_dump(by_alias=True)}


@app.post("/login/cookie", tags=["6. Cookie Сессии"])
async def login_cookie(credentials: LoginRequest, response: Response):
    user_id = str(uuid.uuid4())
    signed_token = signer.sign(f"{user_id}.{int(time.time())}").decode("utf-8")
    response.set_cookie(key="session_token", value=signed_token, httponly=True, max_age=300)
    return {"message": "Успешный вход", "user_id": user_id}


@app.get("/profile/cookie", tags=["6. Cookie Сессии"])
async def get_profile_cookie(session_token: str | None = Cookie(default=None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        signer.unsign(session_token).decode("utf-8")
        return {"message": "Доступ к профилю разрешен"}
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")


def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = auth_db.get(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserInDB = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user


@app.post("/register/jwt", status_code=201, tags=["7. JWT, RBAC и Лимиты"])
@limiter.limit("1/minute")
async def register_jwt(request: Request, user: UserAuth):
    if user.username in auth_db:
        raise HTTPException(status_code=409, detail="User already exists")
    hashed_pw = pwd_context.hash(user.password)
    auth_db[user.username] = UserInDB(username=user.username, role=user.role, hashed_password=hashed_pw)
    return {"message": "New user created"}


@app.post("/login/jwt", response_model=Token, tags=["7. JWT, RBAC и Лимиты"])
@limiter.limit("5/minute")
async def login_jwt(request: Request, user: LoginRequest):
    db_user = auth_db.get(user.username)
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Authorization failed")
    access_token = create_jwt_token(data={"sub": db_user.username, "role": db_user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected_resource", tags=["7. JWT, RBAC и Лимиты"])
async def protected_route(current_user: UserInDB = Depends(get_current_user)):
    return {"message": f"Access granted, {current_user.username}!", "your_role": current_user.role}


@app.get("/admin_only", tags=["7. JWT, RBAC и Лимиты"])
async def admin_only_route(current_user: UserInDB = Depends(RoleChecker(["admin"]))):
    return {"message": "Секретные данные базы", "admin_name": current_user.username}


@app.get("/user_only", tags=["7. JWT, RBAC и Лимиты"])
async def user_only_route(current_user: UserInDB = Depends(RoleChecker(["admin", "user"]))):
    return {"message": "Вы можете читать и обновлять ресурсы"}


@app.post("/register/db", tags=["8. SQLite Database CRUD"])
async def register_to_db(user: UserRegisterDB):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
    conn.commit()
    conn.close()
    return {"message": "User registered successfully!"}


@app.post("/todos", status_code=201, response_model=TodoResponse, tags=["8. SQLite Database CRUD"])
async def create_todo(todo: TodoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
        (todo.title, todo.description),
    )
    todo_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    new_todo = cursor.fetchone()
    conn.close()
    return dict(new_todo)


@app.get("/todos/{todo_id}", response_model=TodoResponse, tags=["8. SQLite Database CRUD"])
async def read_todo(todo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    todo = cursor.fetchone()
    conn.close()

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return dict(todo)


@app.put("/todos/{todo_id}", response_model=TodoResponse, tags=["8. SQLite Database CRUD"])
async def update_todo(todo_id: int, todo: TodoUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")

    cursor.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (todo.title, todo.description, todo.completed, todo_id),
    )
    conn.commit()

    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    updated_todo = cursor.fetchone()
    conn.close()
    return dict(updated_todo)


@app.delete("/todos/{todo_id}", tags=["8. SQLite Database CRUD"])
async def delete_todo(todo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")

    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return {"message": "Todo deleted successfully"}
