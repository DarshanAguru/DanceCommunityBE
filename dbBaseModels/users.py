from pydantic import BaseModel, ConfigDict
from typing import List,Dict
from bson.objectid import ObjectId

class Users(BaseModel):
    id: str | ObjectId = None
    name: str | None = None
    pswd: str | None = None
    type: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    clickTracks: List  = []
    model_config = ConfigDict(arbitrary_types_allowed=True)

