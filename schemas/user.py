from pydantic import BaseModel, ConfigDict, Field


class UserCredentials(BaseModel):
    """Тело запроса для регистрации и входа."""
    model_config = ConfigDict(extra="forbid")

    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=64)


class UserOut(BaseModel):
    """Ответ регистрации: плоско, без вложенности, пароль наружу не отдаётся."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
