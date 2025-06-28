from pydantic import BaseModel


class SongInfoOut(BaseModel):
    title: str
    filename: str
    link: str


class OperationId(BaseModel):
    operation_id: str
