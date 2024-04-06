from pydantic import BaseModel, ConfigDict
from typing import List
from bson.objectid import ObjectId

class Institutions(BaseModel):
    id: str | ObjectId = None
    institutionName: str | None = None
    headOfInstitution: str | None = None
    coursesOffered: str | None = None
    additionalOffers: str | None = None
    location: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

