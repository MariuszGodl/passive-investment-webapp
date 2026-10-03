from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    surname: str
    email: str
    favorites: list[int] = Field(default_factory=list)
