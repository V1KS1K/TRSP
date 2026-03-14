from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, EmailStr, Field, ConfigDict
from fastapi.responses import FileResponse
import uvicorn
import models


app = FastAPI()

@app.get("/", tags=["1.2"])
async def read_index():
    return FileResponse("index.html")

#--------------------------------------------------------------------
num1 = 5
num2 = 10

@app.post("/calculate", tags=["1.3*"])
def calculate1():
    return num1 + num2
#----------------------------------------------------------------------

user_data = models.User(name="Ваше Имя и Фамилия", id=1)

@app.get("/user", tags=["1.4"])
def get_user_info():
    return user_data

#----------------------------------------------------------------------

feedbacks_list = []

@app.post("/feedback", tags=["2.1"])
def create_feedback(feedback: models.Feedback):
    feedbacks_list.append(feedback.model_dump())
    return {"message": f"Feedback received. Thank you, {feedback.name}."}


if __name__ == "__main__":
    uvicorn.app("main.app")



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

