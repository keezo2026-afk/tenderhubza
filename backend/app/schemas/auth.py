from pydantic import BaseModel, EmailStr, Field
class RegisterRequest(BaseModel):
    email: EmailStr; password: str=Field(min_length=10, max_length=128); first_name: str=Field(min_length=1,max_length=100); last_name: str=Field(min_length=1,max_length=100); phone: str|None=Field(default=None,max_length=30)
class LoginRequest(BaseModel): email: EmailStr; password: str
class TokenResponse(BaseModel): access_token: str; token_type: str="bearer"; expires_at: str
