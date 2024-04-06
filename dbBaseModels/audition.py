from pydantic import BaseModel, ConfigDict
from typing import List
from bson.objectid import ObjectId

class Auditions(BaseModel):
    id: str | ObjectId = None
    title: str | None = None
    requirements: str | None = None
    date: str | None = None
    additionalInfo: str | None = None
    location: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    img : str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

