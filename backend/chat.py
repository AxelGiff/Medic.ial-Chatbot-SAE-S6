from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from bson.objectid import ObjectId
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

from auth import get_current_user
from database import get_db
from config import HF_TOKEN, MAX_TOKENS, EMBEDDING_MODEL

router = APIRouter(prefix="/api", tags=["Chat"])
db=get_db()
conversation_history = {}
hf_client = InferenceClient(token=HF_TOKEN)

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("✅ Modèle d'embedding médical chargé avec succès")
except Exception as e:
    print(f"❌ Erreur chargement embedding: {str(e)}")
    embedding_model = None

# Fonctions de RAG
def retrieve_relevant_context(query, embedding_model, mongo_collection, k=5):
    query_embedding = embedding_model.embed_query(query)
    
    docs = list(mongo_collection.find({}, {"text": 1, "embedding": 1}))
    
    print(f"[DEBUG] Recherche de contexte pour: '{query}'")
    print(f"[DEBUG] {len(docs)} documents trouvés dans la base de données")
    
    if not docs:
        print("[DEBUG] Aucun document dans la collection. RAG désactivé.")
        return ""
    
    similarities = []
    for i, doc in enumerate(docs):
        if "embedding" not in doc or not doc["embedding"]:
            print(f"[DEBUG] Document {i} sans embedding")
            continue
            
        sim = cosine_similarity([query_embedding], [doc["embedding"]])[0][0]
        similarities.append((sim, i, doc["text"]))
    
    similarities.sort(reverse=True)
    
    print("\n=== CONTEXTE SÉLECTIONNÉ ===")
    top_k_docs = []
    for i, (score, idx, text) in enumerate(similarities[:k]):
        doc_preview = text[:100] + "..." if len(text) > 100 else text
        print(f"Document #{i+1} (score: {score:.4f}): {doc_preview}")
        top_k_docs.append(text)
    print("==========================\n")
    
    return "\n\n".join(top_k_docs)

@router.post("/chat")
async def chat(request: Request):
    global conversation_history
    
    data = await request.json()
    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    skip_save = data.get("skip_save", False)


    if not skip_save and conversation_id and current_user: 
        db.messages.insert_one({
            "conversation_id": conversation_id,
            "user_id": str(current_user["_id"]),
            "sender": "user",
            "text": user_message,
            "timestamp": datetime.utcnow()
        })

   
        
    if not user_message:
        raise HTTPException(status_code=400, detail="Le champ 'message' est requis.")

    current_user = None
    try:
        current_user = await get_current_user(request)
    except HTTPException:
        pass

    current_tokens = 0
    message_tokens = 0
    if current_user and conversation_id:
        conv = db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": str(current_user["_id"])
        })
        if conv:
            current_tokens = conv.get("token_count", 0)
        message_tokens = int(len(user_message.split()) * 1.3)
        MAX_TOKENS = 2000
        if current_tokens + message_tokens > MAX_TOKENS:
            return JSONResponse({
                "error": "token_limit_exceeded",
                "message": "Cette conversation a atteint sa limite de taille. Veuillez en créer une nouvelle.",
                "tokens_used": current_tokens,
                "tokens_limit": MAX_TOKENS
            }, status_code=403)

    

    is_history_question = any(
        phrase in user_message.lower()
        for phrase in [
            "ma première question", "ma précédente question", "ma dernière question",
            "ce que j'ai demandé", "j'ai dit quoi", "quelles questions",
            "c'était quoi ma", "quelle était ma", "mes questions", "questions précédentes"
        ]
    ) or re.search(r"(?:quelle|quelles|quoi).*?(\d+)[a-z]{2}.*?question", user_message.lower()) \
       or re.search(r"derni[eè]re question", user_message.lower()) \
       or re.search(r"premi[eè]re question", user_message.lower()) \
       or re.search(r"question pr[eé]c[eé]dente", user_message.lower()) \
       or re.search(r"(toutes|liste|quelles|quoi).*questions", user_message.lower())

    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = []
        if current_user and conversation_id:
            previous_messages = list(db.messages.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", 1))
            
            for msg in previous_messages:
                if msg["sender"] == "user":
                    conversation_history[conversation_id].append(f"Question : {msg['text']}")
                else:
                    conversation_history[conversation_id].append(f"Réponse : {msg['text']}")

    if is_history_question:
        actual_questions = []
        
        if conversation_id in conversation_history:
            for msg in conversation_history[conversation_id]:
                if msg.startswith("Question : "):
                    q_text = msg.replace("Question : ", "")
                    is_meta = any(phrase in q_text.lower() for phrase in [
                        "ma première question", "ma précédente question", "ma dernière question",
                        "ce que j'ai demandé", "j'ai dit quoi", "quelles questions",
                        "c'était quoi ma", "quelle était ma", "mes questions"
                    ]) or re.search(r"(?:quelle|quelles|quoi).*?(\d+)[a-z]{2}.*?question", q_text.lower()) \
                       or re.search(r"derni[eè]re question", q_text.lower()) \
                       or re.search(r"premi[eè]re question", q_text.lower()) \
                       or re.search(r"question pr[eé]c[eé]dente", q_text.lower()) \
                       or re.search(r"(toutes|liste|quelles|quoi).*questions", q_text.lower())
                    if not is_meta:
                        actual_questions.append(q_text)
        
        if not actual_questions:
            return JSONResponse({
                "response": "Vous n'avez pas encore posé de question dans cette conversation. C'est notre premier échange."
            })
            
        if re.search(r"derni[eè]re question", user_message.lower()):
            return JSONResponse({
                "response": f"Votre dernière question était : « {actual_questions[-1]} »"
            })
            
        if re.search(r"question pr[eé]c[eé]dente", user_message.lower()):
            if len(actual_questions) >= 2:
                return JSONResponse({
                    "response": f"Votre question précédente était : « {actual_questions[-2]} »"
                })
            else:
                return JSONResponse({
                    "response": "Il n'y a pas encore de question précédente dans notre conversation."
                })
                
        if re.search(r"premi[eè]re question", user_message.lower()) or any(p in user_message.lower() for p in ["première question", "1ère question", "1ere question"]):
            return JSONResponse({
                "response": f"Votre première question était : « {actual_questions[0]} »"
            })
            
        match_nth = re.search(r"(?:quelle|quelles|quoi).*?(\d+)[a-z]{2}.*?question", user_message.lower())
        if match_nth:
            try:
                question_number = int(match_nth.group(1))
                if 0 < question_number <= len(actual_questions):
                    return JSONResponse({
                        "response": f"Votre {question_number}{'ère' if question_number == 1 else 'ème'} question était : « {actual_questions[question_number-1]} »"
                    })
                else:
                    return JSONResponse({
                        "response": f"Vous n'avez pas encore posé {question_number} questions dans cette conversation."
                    })
            except:
                pass
        
        question_number = None
        if any(p in user_message.lower() for p in ["deuxième question", "2ème question", "2eme question", "seconde question"]):
            question_number = 2
        else:
            match = re.search(r'(\d+)[eèiéê]*m*e* question', user_message.lower())
            if match:
                try:
                    question_number = int(match.group(1))
                except:
                    pass
        
        if question_number is not None:
            if 0 < question_number <= len(actual_questions):
                suffix = "ère" if question_number == 1 else "ème"
                return JSONResponse({
                    "response": f"Votre {question_number}{suffix} question était : « {actual_questions[question_number-1]} »"
                })
            else:
                return JSONResponse({
                    "response": f"Vous n'avez pas encore posé {question_number} questions dans cette conversation."
                })
        
        if len(actual_questions) == 1:
            return JSONResponse({
                "response": f"Vous avez posé une seule question jusqu'à présent : « {actual_questions[0]} »"
            })
        else:
            question_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(actual_questions)])
            return JSONResponse({
                "response": f"Voici les questions que vous avez posées dans cette conversation :\n\n{question_list}"
            })

    context = None
    if not is_history_question and embedding_model:
        context = retrieve_relevant_context(user_message, embedding_model, db.connaissances, k=5)
        if context and conversation_id:
            conversation_history[conversation_id].append(f"Contexte : {context}")

    if conversation_id:
        conversation_history[conversation_id].append(f"Question : {user_message}")

    system_prompt = (
    "Tu es un chatbot spécialisé dans la santé mentale, et plus particulièrement la schizophrénie. "
    "Tu réponds de façon fiable, claire et empathique, en t'appuyant uniquement sur des sources médicales et en français. "
    "IMPORTANT: Fais particulièrement attention aux questions de suivi. Si l'utilisateur pose une question qui ne précise "
    "pas clairement le sujet mais qui fait suite à votre échange précédent, comprends que cette question fait référence "
    "au contexte de la conversation précédente. Par exemple, si l'utilisateur demande 'Comment les traite-t-on?' après "
    "avoir parlé des symptômes positifs de la schizophrénie, ta réponse doit porter spécifiquement sur le traitement "
    "des symptômes positifs, et non sur la schizophrénie en général.IMPORTANT: Vise tes réponses sous forme de Markdown."
)

    enriched_context = ""

    if conversation_id in conversation_history:
        actual_questions = []
        for msg in conversation_history[conversation_id]:
            if msg.startswith("Question : "):
                q_text = msg.replace("Question : ", "")
                is_meta = any(phrase in q_text.lower() for phrase in [
                    "ma première question", "ma précédente question", "ma dernière question",
                    "ce que j'ai demandé", "j'ai dit quoi", "quelles questions",
                    "c'était quoi ma", "quelle était ma", "mes questions"
                ]) or re.search(r"(?:quelle|quelles|quoi).*?(\d+)[a-z]{2}.*?question", q_text.lower()) \
                   or re.search(r"derni[eè]re question", q_text.lower()) \
                   or re.search(r"premi[eè]re question", q_text.lower()) \
                   or re.search(r"question pr[eé]c[eé]dente", q_text.lower()) \
                   or re.search(r"(toutes|liste|quelles|quoi).*questions", q_text.lower())
                if not is_meta and q_text != user_message:  
                    actual_questions.append(q_text)
        
        if actual_questions:
            recent_questions = actual_questions[-5:] 
            enriched_context += "Historique récent des questions:\n"
            for i, q in enumerate(recent_questions):
                enriched_context += f"- Question précédente {len(recent_questions)-i}: {q}\n"
            enriched_context += "\n"

    if context:
        enriched_context += "Contexte médical pertinent:\n"
        enriched_context += context
        enriched_context += "\n\n"

    if enriched_context:
        system_prompt += (
            f"\n\n{enriched_context}\n\n"
            "Utilise ces informations pour répondre de manière plus précise et contextuelle. "
            "Ne pas inventer d'informations. Si tu ne sais pas, redirige vers un professionnel de santé. "
            "Tu dois donner une réponse complète, bien structurée et ne jamais couper ta réponse brutalement. "
            "Si tu n'as pas assez de place pour finir, indique-le clairement à l'utilisateur."
        )
    else:
        system_prompt += (
            "Tu dois répondre uniquement à partir de connaissances médicales factuelles. "
            "Si tu ne sais pas répondre, indique-le clairement et suggère de consulter un professionnel de santé. "
            "Tu dois donner une réponse complète et bien structurée."
        )

    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_id and len(conversation_history.get(conversation_id, [])) > 0:
        history = conversation_history[conversation_id]
        for i in range(0, min(20, len(history)-1), 2):
            if i+1 < len(history):
                if history[i].startswith("Question :"):
                    user_text = history[i].replace("Question : ", "")
                    messages.append({"role": "user", "content": user_text})
                
                if history[i+1].startswith("Réponse :"):
                    assistant_text = history[i+1].replace("Réponse : ", "")
                    messages.append({"role": "assistant", "content": assistant_text})
    
    messages.append({"role": "user", "content": user_message})

    try:
        completion = hf_client.chat.completions.create(
            model="mistralai/Mistral-Small-24B-Instruct-2501", 
            messages=messages,
            max_tokens=1024,  
            temperature=0.7, 
            timeout=15,  
        )
        bot_response = completion.choices[0].message["content"].strip()
        if bot_response.endswith((".", "!", "?")) == False and len(bot_response) > 500:
            bot_response += "\n\n(Note: Ma réponse a été limitée par des contraintes de taille. N'hésitez pas à me demander de poursuivre si vous souhaitez plus d'informations.)"
    except Exception:
        try:
            fallback = hf_client.text_generation(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                prompt=f"<s>[INST] {system_prompt}\n\nQuestion: {user_message} [/INST]",
                max_new_tokens=512,
                temperature=0.7
            )
            bot_response = fallback
        except Exception:
            bot_response = "Je suis désolé, je rencontre actuellement des difficultés techniques. Pourriez-vous reformuler votre question ou réessayer dans quelques instants?"

    if conversation_id:
        conversation_history[conversation_id].append(f"Réponse : {bot_response}")
        
        if len(conversation_history[conversation_id]) > 50: 
            conversation_history[conversation_id] = conversation_history[conversation_id][-50:]

    if not skip_save and conversation_id and current_user: 
        db.messages.insert_one({
            "conversation_id": conversation_id,
            "user_id": str(current_user["_id"]),
            "sender": "bot", 
            "text": bot_response,
            "timestamp": datetime.utcnow()
        })

    if conversation_id and current_user:
        db.messages.insert_one({
            "conversation_id": conversation_id,
            "user_id": str(current_user["_id"]),
            "sender": "bot", 
            "text": bot_response,
            "timestamp": datetime.utcnow()
        })
        response_tokens = int(len(bot_response.split()) * 1.3)
        total_tokens = current_tokens + message_tokens + response_tokens
        db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {
                "last_message": bot_response,
                "updated_at": datetime.utcnow(),
                "token_count": total_tokens
            }}
        )

    return {"response": bot_response}