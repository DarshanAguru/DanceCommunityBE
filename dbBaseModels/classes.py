from pydantic import BaseModel, ConfigDict
from bson.objectid import ObjectId

class Classes(BaseModel):
    id: str | ObjectId = None
    userId: str | ObjectId = None
    danceFormName: str | None = None
    teacherName: str | None = None
    className: str | None = None
    videoLink: str | None =  None
    img : str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

