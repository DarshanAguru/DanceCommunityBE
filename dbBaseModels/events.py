from pydantic import BaseModel, ConfigDict
from typing import List
from bson.objectid import ObjectId

class Events(BaseModel):
    id: str | ObjectId = None
    title: str | None = None
    date: str | None = None
    timings: str | None = None
    venue: str | None = None
    img : str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

