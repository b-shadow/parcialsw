from pydantic import BaseModel, EmailStr, Field


class SolicitudRegistro(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SolicitudIngreso(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RespuestaToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

