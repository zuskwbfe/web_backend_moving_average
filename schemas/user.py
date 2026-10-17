from pydantic import BaseModel, ConfigDict, Field


class UserCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
