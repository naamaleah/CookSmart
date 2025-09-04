# backend/api/routers/images.py
from fastapi import APIRouter, UploadFile, File, Depends
from backend.gateway import Gateway
from backend.api.deps import get_gateway

router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/upload")
async def upload_image(
    image: UploadFile = File(...),
    gateway: Gateway = Depends(get_gateway),
):
    """
    Upload an image to Cloudinary and return its secure URL.
    This endpoint is separate to keep recipe commands clean.
    """
    file_bytes = await image.read()
    uploaded = await gateway.cloudinary_upload_image(file_bytes, image.filename)
    return {"secure_url": uploaded.secure_url}
