from pydantic import BaseModel

class BasicResponse(BaseModel):
    message: str


class EditRequest(BaseModel):
    cell_type: str