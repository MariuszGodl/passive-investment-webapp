from pydantic import BaseModel, Field


class User(BaseModel):
    full_name: str
    email: str
    favorites: list[int] = Field(default_factory=list)
    password: str
