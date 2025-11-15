from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List
from .service import SampleService
from .schemas import EditRequest
from common.schemas import BasicResponse
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    name = file.filename
    fileName = name[:name.index("_")]
    result = SampleService.save(db=db, file_stream=content, file_name=fileName)
    success = result.get("success")
    message = ""
    if success:
        message = "File uploaded successfully"
    else:
        message = f"File uploaded unsuccessfully, file name {file.filename} already existed"
    return BasicResponse(message=message)


@router.post("/many")
async def upload_multiple_files(
    files: List[UploadFile] = File(...), db: Session = Depends(get_db)
):
    file_streams = []
    names = []
    for file in files:
        content = await file.read()
        file_streams.append(content)
        name = file.filename
        fileName = name[:name.index("_")]
        names.append(fileName)
    result = SampleService.save_many(db=db, files=file_streams, names=names)
    # result có thể là dict như: {"added": [...], "skipped": [...]}
    added = result.get("added", [])
    skipped = result.get("skipped", [])

    # Tạo thông điệp phản hồi
    message = f"Uploaded {len(added)} file(s) successfully."
    if skipped:
        message += f" Skipped {len(skipped)} duplicate name(s): {', '.join(skipped)}."
    return BasicResponse(message="Files uploaded successfully")


@router.get("/{sample_id}")
def get_sample(sample_id: str, db: Session = Depends(get_db)):
    sample = SampleService.get(sample_id=sample_id, db=db)
    if sample:
        return sample
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
    )


@router.get("/")
def get_all_samples(db: Session = Depends(get_db)):
    return SampleService.get_all(db=db)


@router.delete("/{sample_id}")
def delete_sample(sample_id: str, db: Session = Depends(get_db)):
    SampleService.delete(sample_id=sample_id, db=db)
    return BasicResponse(message="Sample deleted successfully")


@router.get("/{sample_id}/download")
def get_sample_file(sample_id: str, db: Session = Depends(get_db)):
    file = SampleService.get_file_by_id(sample_id=sample_id, db=db)
    file.seek(0)
    if file:
        return StreamingResponse(
            file,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={sample_id}.bam"},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.post("/{sample_id}")
def update_sample(sample_id: str, request: EditRequest, db: Session = Depends(get_db)):
    sample = SampleService.update(db=db, sample=sample_id, request=request)
    if sample:
        return BasicResponse(message="Sample updated successfully")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
    )
