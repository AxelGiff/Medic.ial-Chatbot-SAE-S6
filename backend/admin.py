from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from bson.objectid import ObjectId
import os
import PyPDF2
from io import BytesIO
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from auth import get_admin_user
from database import get_db
from config import SAVE_FOLDER
from chat import embedding_model

router = APIRouter(prefix="/api/admin", tags=["Administration"])
db=get_db()

# Fonction pour téleverser un document PDF.
#Découpe le PDF en plusieurs chunks 
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
        
        # Extraction du texte du PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        for page_num in range(len(pdf_reader.pages)):
            text_content += pdf_reader.pages[page_num].extract_text() + "\n"
        
        # Générer un ID pour le document principal
        doc_id = ObjectId()
        
        # Sauvegarder le fichier PDF
        pdf_path = f"files/{str(doc_id)}.pdf"
        os.makedirs("files", exist_ok=True)
        with open(pdf_path, "wb") as f:
            pdf_file.seek(0)
            f.write(contents)
        
        # Découper le document en chunks
        print(f"Découpage du document '{title or file.filename}' en chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        
        # Document Langchain pour le splitting
        doc = Document(page_content=text_content, metadata={"title": title or file.filename})
        chunks = splitter.split_documents([doc])
        print(f"{len(chunks)} morceaux extraits.")
        
        # Insérer le document principal pour référence
        main_document = {
            "_id": doc_id,
            "title": title or file.filename,
            "tags": tags.split(",") if tags else [],
            "uploaded_by": str(current_user["_id"]),
            "upload_date": datetime.utcnow(),
            "is_parent": True,
            "chunk_count": len(chunks),
            "file_path": pdf_path
        }
        
        db.connaissances.insert_one(main_document)
        
        # Générer et insérer les chunks
        inserted_chunks = 0
        chunk_ids = []
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_text = chunk.page_content
                if len(chunk_text) > 5000:  
                    chunk_text = chunk_text[:5000]
                
                # Générer l'embedding
                embedding = None
                if embedding_model:
                    try:
                        embedding = embedding_model.embed_query(chunk_text)
                    except Exception as e:
                        print(f"Erreur lors de la génération de l'embedding pour le morceau {i+1}: {str(e)}")
                
                # Créer un document pour ce chunk
                chunk_id = ObjectId()
                chunk_doc = {
                    "_id": chunk_id,
                    "parent_id": doc_id,
                    "text": chunk_text,
                    "embedding": embedding,
                    "title": f"{title or file.filename} - Partie {i+1}",
                    "tags": tags.split(",") if tags else [],
                    "chunk_index": i,
                    "uploaded_by": str(current_user["_id"]),
                    "upload_date": datetime.utcnow(),
                    "is_chunk": True
                }
                
                # Insérer le chunk dans la base de données
                db.connaissances.insert_one(chunk_doc)
                chunk_ids.append(str(chunk_id))
                inserted_chunks += 1
                
                print(f"Morceau {i+1}/{len(chunks)} inséré.")
            except Exception as chunk_error:
                print(f"Erreur lors du traitement du morceau {i+1}: {str(chunk_error)}")
        
        # Mettre à jour le document parent avec les IDs des chunks
        db.connaissances.update_one(
            {"_id": doc_id},
            {"$set": {"chunk_ids": chunk_ids, "inserted_chunks": inserted_chunks}}
        )
        
        # Vérification
        verification = db.connaissances.find_one({"_id": doc_id})
        if verification:
            print(f"Document parent vérifié et trouvé dans la base de données avec {inserted_chunks} chunks")
            return {
                "success": True, 
                "document_id": str(doc_id),
                "chunks_total": len(chunks),
                "chunks_inserted": inserted_chunks
            }
        else:
            print(f"ERREUR: Document parent non trouvé après insertion")
            return {
                "success": False, 
                "error": "Document parent non trouvé après insertion"
            }
        
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

#Fonction pour supprimer un document. Si on supprimer le document principal, on supprime également tous les chunks qui en dépendent.
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
        
        chunks_deleted = 0
        if document.get("is_parent", False):
            chunks_result = db.connaissances.delete_many({"parent_id": doc_id})
            chunks_deleted = chunks_result.deleted_count
            print(f"Suppression de {chunks_deleted} chunks associés au document {document_id}")
        
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
        
        return {
            "success": True, 
            "message": f"Document supprimé avec succès, ainsi que {chunks_deleted} chunks associés"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")
