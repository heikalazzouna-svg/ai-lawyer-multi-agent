from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Annotated
from api.routers.auth import get_current_user

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a legal document. Requires authentication.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # In a real application, save the file and call vector_database.index_pdf()
    return {
        "filename": file.filename, 
        "status": "indexed",
        "owner": current_user["username"]
    }

@router.get("/")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """
    List documents owned by the current user.
    """
    # Mock response
    return [
        {"filename": "contract.pdf", "status": "indexed"}
    ]
