from fastapi import APIRouter, Request, HTTPException, Depends
from datetime import datetime
from bson.objectid import ObjectId

from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api", tags=["Conversations"])
db = get_db()
#Fonction qui retourne la dernière conversation
@router.get("/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        
        conversations = list(db.conversations.find(
            {"user_id": user_id},
            {"_id": 1, "title": 1, "date": 1, "time": 1, "last_message": 1, "created_at": 1}
        ).sort("created_at", -1))
        
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

#Fonction qui créer une conversation quand on l'appel 

@router.post("/conversations")
async def create_conversation(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
        user_id = str(current_user["_id"])
        
        conversation = {
            "user_id": user_id,
            "title": data.get("title", "Nouvelle conversation"),
            "date": data.get("date"),
            "time": data.get("time"),
            "last_message": data.get("message", ""),
            "created_at": datetime.utcnow()
        }
        
        result = db.conversations.insert_one(conversation)
        
        return {"conversation_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

#Fonction qui créer les messagees d'une conversation

@router.post("/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
        user_id = str(current_user["_id"])
        
        print(f"Ajout message: conversation_id={conversation_id}, sender={data.get('sender')}, text={data.get('text')[:20]}...")
        
        conversation = db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        message = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "sender": data.get("sender", "user"),
            "text": data.get("text", ""),
            "timestamp": datetime.utcnow()
        }
        
        db.messages.insert_one(message)
        
        db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"last_message": data.get("text", ""), "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True}
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

#Fonction qui récupère les messages de la conversation cliquée
@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        
        conversation = db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        messages = list(db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1))
        
        deduplicated_messages = []
        seen_texts = set()
        
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            
            if "timestamp" in msg:
                msg["timestamp"] = msg["timestamp"].isoformat()
            
            timestamp_rounded = msg.get("timestamp", "")[:19]  
            dedup_key = f"{msg['sender']}:{msg['text'][:50]}:{timestamp_rounded}"
            
            if dedup_key not in seen_texts:
                seen_texts.add(dedup_key)
                deduplicated_messages.append(msg)
                
                if msg["sender"] == "assistant" and deduplicated_messages and deduplicated_messages[-1]["sender"] == "bot":
                    if deduplicated_messages[-1]["text"] == msg["text"]:
                        deduplicated_messages.pop()
        
        return {"messages": deduplicated_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

#Fonction qui supprime une conversation donnée

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user["_id"])
        
        result = db.conversations.delete_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        db.messages.delete_many({"conversation_id": conversation_id})
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
