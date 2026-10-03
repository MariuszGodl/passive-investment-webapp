from pydantic import BaseModel


class User(BaseModel):
    name: str
    surname: str
    email: str
