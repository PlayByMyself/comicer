from typing import List, Optional
from pydantic import BaseModel, HttpUrl, SecretStr


class Source(BaseModel):
    start_url: HttpUrl
    login_url: HttpUrl
    username: Optional[str]
    password: Optional[SecretStr]
    username_selector: str
    password_selector: str
    login_submit_selector: str
    favorite_url_selector: str
    download_url_selector: str
    download_url_text: List[str]
    title_selector: str
