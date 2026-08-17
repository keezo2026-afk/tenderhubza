from typing import Any
from fastapi import HTTPException
class ApiError(HTTPException):
    def __init__(self,status_code:int,code:str,message:str,details:Any|None=None,headers:dict|None=None):
        super().__init__(status_code=status_code,detail=message,headers=headers);self.code=code;self.message=message;self.details=details or {}
def error_body(code:str,message:str,details:Any|None=None)->dict: return {"error":{"code":code,"message":message,"details":details or {}}}
