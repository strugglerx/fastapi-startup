'''
Description: 
Author: Moqi
Date: 2025-07-04 10:23:06
Email: str@li.cm
Github: https://github.com/strugglerx
LastEditors: Moqi
LastEditTime: 2025-07-04 10:33:27
'''
from pydantic import BaseModel
from typing import Optional

class LoginReq(BaseModel):
    account: str
    password: str       