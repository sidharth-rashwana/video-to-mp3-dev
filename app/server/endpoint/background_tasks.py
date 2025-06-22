from fastapi import APIRouter,HTTPException,UploadFile,File
from celery.result import AsyncResult
from app.server.config.celery_tasks import convert_mp4_to_mp3,extract_audio_section_from_video
from fastapi.responses import StreamingResponse
from app.server.utils.token import get_current_active_user
from app.server.model.token  import User 
from fastapi import Depends,status
from typing import Annotated
from celery.exceptions import TimeoutError

router = APIRouter()

@router.post("/convert/video")
async def convert_video_to_audio(current_user: Annotated[User, Depends(get_current_active_user)],file: UploadFile = File(...)):
    if current_user.role not in ['ADMIN','USER']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='You are not authorize to access this API.',
                                    headers={"WWW-Authenticate": "Bearer"})
    if file.content_type != "video/mp4":
        raise HTTPException(status_code=400, detail="Only MP4 files are allowed.")

    result = convert_mp4_to_mp3.delay(file.filename, file.file.read())

    return {"task_id": result.id, "status": "Conversion process started."}

@router.post("/extract/audio")
async def extract_audio_from_video(current_user: Annotated[User, Depends(get_current_active_user)], start_time: float, end_time: float, file: UploadFile = File(...)):
    if current_user.role not in ['ADMIN', 'USER']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='You are not authorized to access this API.',
                            headers={"WWW-Authenticate": "Bearer"})
    
    if file.content_type != "video/mp4":
        raise HTTPException(status_code=400, detail="Only MP4 files are allowed.")

    result = extract_audio_section_from_video.delay(file.filename, file.file.read(), start_time, end_time)

    return {"task_id": result.id, "status": "Audio extraction process started."}


@router.get("/progress/{task_id}")
async def read_task_status(task_id: str, current_user: User = Depends(get_current_active_user)):
    if current_user.role not in ['ADMIN', 'USER']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='You are not authorized to access this API.',
                            headers={"WWW-Authenticate": "Bearer"})

    task_result = AsyncResult(task_id)
    if task_result.state == 'PENDING':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Task with the provided ID does not exist.')

    if task_result.ready():
        if task_result.successful():
            return {"status": "Conversion successful"}  # "result":task_result.result: You can include more details such as output path if needed
        else:
            return {"status": "Conversion failed", "error": str(task_result.result)}
    else:
        return {"status": "Conversion in progress"}

@router.get("/download/{task_id}")
async def download_converted_file(task_id: str, current_user: User = Depends(get_current_active_user)):
    if current_user.role not in ['ADMIN', 'USER']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='You are not authorized to access this API.',
                            headers={"WWW-Authenticate": "Bearer"})

    task_result = AsyncResult(task_id, app=convert_mp4_to_mp3)
    
    if task_result.state == 'PENDING':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Task with the provided ID does not exist.')
        
    if task_result.ready():
        if task_result.successful():
            if 'output_path' not in task_result.result:
                raise HTTPException(status_code=404, detail="Conversion of file was not successful.")
            converted_file_path = task_result.result.get('output_path')
            if converted_file_path:
                return StreamingResponse(open(converted_file_path, "rb"), 
                                         media_type="audio/mp3", 
                                         headers={"Content-Disposition": f"attachment; filename={task_id}.mp3"})
            else:
                raise HTTPException(status_code=404, detail="Converted file path not found.")
        else:
            raise HTTPException(status_code=404, detail="Conversion failed.")
    else:
        raise HTTPException(status_code=404, detail="Not ready to download.")
