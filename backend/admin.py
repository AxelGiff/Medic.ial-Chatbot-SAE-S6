from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from bson.objectid import ObjectId
import os
import PyPDF2
from io import BytesIO
from datetime import datetime

from auth import get_admin_user
from database import get_db
from config import SAVE_FOLDER
from chat import embedding_model

router = APIRouter(prefix="/api/admin", tags=["Administration"])
db=get_db()

@router.post("/knowledge/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = None,
    tags: str = None,
    current_user: dict = Depends(get_admin_user)
):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
        
        contents = await file.read()
        pdf_file = BytesIO(contents)
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        for page_num in range(len(pdf_reader.pages)):
            text_content += pdf_reader.pages[page_num].extract_text() + "\n"
        
        embedding = None
        if embedding_model:
            try:
                max_length = 5000
                truncated_text = text_content[:max_length]
                embedding = embedding_model.embed_query(truncated_text).tolist()
            except Exception as e:
                print(f"Erreur lors de la génération de l'embedding: {str(e)}")
        
        doc_id = ObjectId()
        
        pdf_path = f"files/{str(doc_id)}.pdf"
        os.makedirs("files", exist_ok=True)
        with open(pdf_path, "wb") as f:
            pdf_file.seek(0)
            f.write(contents)
        
        document = {
            "_id": doc_id,
            "text": text_content,
            "embedding": embedding,
            "title": title or file.filename,
            "tags": tags.split(",") if tags else [],
            "uploaded_by": str(current_user["_id"]),
            "upload_date": datetime.utcnow()
        }
        
        print(f"Tentative d'insertion du document avec ID: {doc_id}")
        result = db.connaissances.insert_one(document)
        print(f"Document inséré avec ID: {result.inserted_id}")
        
        verification = db.connaissances.find_one({"_id": doc_id})
        if verification:
            print(f"Document vérifié et trouvé dans la base de données")
            return {"success": True, "document_id": str(doc_id)}
        else:
            print(f"ERREUR: Document non trouvé après insertion")
            return {"success": False, "error": "Document non trouvé après insertion"}
        
    except Exception as e:
        import traceback
        print(f"Erreur lors de l'upload du PDF: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.get("/knowledge")
async def list_documents(current_user: dict = Depends(get_admin_user)):
    try:
        documents = list(db.connaissances.find().sort("upload_date", -1))
        
        result = []
        for doc in documents:
            doc_safe = {
                "id": str(doc["_id"]),
                "title": doc.get("title", "Sans titre"),
                "tags": doc.get("tags", []),
                "date": doc.get("upload_date").isoformat() if "upload_date" in doc else None,
                "text_preview": doc.get("text", "")[:100] + "..." if len(doc.get("text", "")) > 100 else doc.get("text", "")
            }
            result.append(doc_safe)
        
        return {"documents": result}
    except Exception as e:
        print(f"Erreur lors de la liste des documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.delete("/knowledge/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_admin_user)):
    try:
        try:
            doc_id = ObjectId(document_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de document invalide")
        
        document = db.connaissances.find_one({"_id": doc_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        result = db.connaissances.delete_one({"_id": doc_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Échec de la suppression du document")
        
        pdf_path = f"files/{document_id}.pdf"
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Fichier supprimé: {pdf_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier: {str(e)}")
        
        return {"success": True, "message": "Document supprimé avec succès"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")