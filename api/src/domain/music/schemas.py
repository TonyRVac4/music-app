from io import BytesIO
from pydantic import BaseModel, ConfigDict


class FileInfoResponse(BaseModel):
    title: str
    filename: str
    duration: float
    link: str


class OperationId(BaseModel):
    operation_id: str


class FileDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: BytesIO | None = None
    title: str
    filename: str
    duration: float
