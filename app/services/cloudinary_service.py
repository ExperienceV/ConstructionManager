from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings


LOCAL_UPLOAD_ROOT = Path("static/uploads")


def _cloudinary_configured() -> bool:
    return all(
        [
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET,
        ]
    )


async def subir_archivo(file: UploadFile, carpeta: str) -> dict:
    if _cloudinary_configured():
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        result = cloudinary.uploader.upload(
            file.file,
            folder=carpeta.strip("/"),
            resource_type="auto",
            use_filename=True,
            unique_filename=True,
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}

    suffix = Path(file.filename or "archivo").suffix
    safe_folder = carpeta.strip("/").replace("..", "").replace("\\", "/")
    target_dir = LOCAL_UPLOAD_ROOT / safe_folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}{suffix}"
    target = target_dir / filename
    content = await file.read()
    target.write_bytes(content)
    public_id = f"local:{safe_folder}/{filename}"
    return {"url": f"/static/uploads/{safe_folder}/{filename}", "public_id": public_id}


def eliminar_archivo(public_id: str) -> bool:
    if not public_id:
        return False

    if public_id.startswith("local:"):
        relative_path = public_id.removeprefix("local:")
        target = LOCAL_UPLOAD_ROOT / relative_path
        if target.exists():
            target.unlink()
        return True

    if _cloudinary_configured():
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        result = cloudinary.uploader.destroy(public_id, resource_type="auto")
        return result.get("result") in {"ok", "not found"}

    return False
