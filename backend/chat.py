from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
from bson.objectid import ObjectId
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import json

from auth import get_current_user
from database import get_db
from config import HF_TOKEN, MAX_TOKENS, EMBEDDING_MODEL

router = APIRouter(prefix="/api", tags=["Chat"])
db=get_db()
conversation_history = {}
hf_client = InferenceClient(token=HF_TOKEN)

def save_bot_response(conversation_id, current_user, text, current_tokens=0, message_tokens=0):
    """Fonction utilitaire pour sauvegarder toutes les réponses du bot"""
    if not conversation_id or not current_user:
        print("⚠️ Impossible de sauvegarder la réponse - conversation_id ou current_user manquant")
        return None
    
    try:
        # Sauvegarder le message
        message_id = db.messages.insert_one({
            "conversation_id": conversation_id,
            "user_id": str(current_user["_id"]),
            "sender": "bot", 
            "text": text,
            "timestamp": datetime.utcnow()
        }).inserted_id
        
        # Mettre à jour les métadonnées de la conversation
        response_tokens = int(len(text.split()) * 1.3) if text else 0
        total_tokens = current_tokens + message_tokens + response_tokens
        
        db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {
                "last_message": text[:100] + ("..." if len(text) > 100 else ""),
                "updated_at": datetime.utcnow(),
                "token_count": total_tokens
            }}
        )
        
        print(f"✅ Réponse du bot sauvegardée avec ID: {message_id}")
        return message_id
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {str(e)}")
        return None

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("Modèle d'embedding médical chargé avec succès")
except Exception as e:
    print(f"Erreur chargement embedding: {str(e)}")
    embedding_model = None

# Fonction de RAG (inchangée)
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

    if not user_message:
        raise HTTPException(status_code=400, detail="Le champ 'message' est requis.")

    current_user = None
    try:
        current_user = await get_current_user(request)
    except HTTPException:
        pass

    # Sauvegarde du message utilisateur (si non anonyme)
    if not skip_save and conversation_id and current_user: 
        db.messages.insert_one({
            "conversation_id": conversation_id,
            "user_id": str(current_user["_id"]),
            "sender": "user",
            "text": user_message,
            "timestamp": datetime.utcnow()
        })

    # Vérification des limites de tokens
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
        if current_tokens + message_tokens > MAX_TOKENS:
            error_message = "⚠️ **Limite de taille de conversation atteinte**\n\nCette conversation est devenue trop longue. Pour continuer à discuter, veuillez créer une nouvelle conversation."
            
            # Sauvegarder ce message d'erreur dans la BD
            if conversation_id and current_user:
                save_bot_response(conversation_id, current_user, error_message, current_tokens, message_tokens)
            
            return JSONResponse({
                "error": "token_limit_exceeded",
                "message": error_message,
                "tokens_used": current_tokens,
                "tokens_limit": MAX_TOKENS
            }, status_code=403)

    # Détection des questions sur l'historique
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

    # Initialisation de l'historique si nécessaire
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

    # Traitement spécial pour les questions sur l'historique
    if is_history_question:
        # Extraire les questions réelles (non meta)
        actual_questions = []
        
        if conversation_id in conversation_history:
            for msg in conversation_history[conversation_id]:
                if msg.startswith("Question : "):
                    q_text = msg.replace("Question : ", "")
                    # Vérifier si ce n'est pas une méta-question
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
        
        # Préparer la réponse en fonction du type spécifique de question
        history_response = ""
        
        if not actual_questions:
            history_response = "Vous n'avez pas encore posé de question dans cette conversation. C'est notre premier échange."
        else:
            # Rechercher des mots-clés spécifiques pour personnaliser la réponse
            
            # Cas 1: Question précédente/dernière question
            if any(phrase in user_message.lower() for phrase in ["question précédente", "dernière question"]) and len(actual_questions) > 1:
                # La dernière question est l'avant-dernière du tableau (la dernière étant la question actuelle)
                prev_question = actual_questions[-1] if actual_questions else "Aucune question précédente trouvée."
                history_response = f"**Votre question précédente était :**\n\n\"{prev_question}\""
            
            # Cas 2: Première question
            elif any(phrase in user_message.lower() for phrase in ["première question", "1ère question", "1ere question"]):
                first_question = actual_questions[0] if actual_questions else "Aucune première question trouvée."
                history_response = f"**Votre première question était :**\n\n\"{first_question}\""
            
            # Cas 3: Question numérotée spécifique (2ème, 3ème, etc.)
            elif re.search(r"(\d+)[èeme]{1,3}", user_message.lower()):
                match = re.search(r"(\d+)[èeme]{1,3}", user_message.lower())
                if match:
                    question_num = int(match.group(1))
                    if 0 < question_num <= len(actual_questions):
                        specific_question = actual_questions[question_num-1]
                        history_response = f"**Votre question n°{question_num} était :**\n\n\"{specific_question}\""
                    else:
                        history_response = f"Je ne trouve pas de question n°{question_num} dans notre conversation. Vous n'avez posé que {len(actual_questions)} question(s)."
            
            # Cas par défaut: Toutes les questions
            else:
                history_response = "**Voici les questions que vous avez posées dans cette conversation :**\n\n"
                for i, question in enumerate(actual_questions, 1):
                    history_response += f"{i}. {question}\n"
                    
                # Ajouter des informations supplémentaires pour les longues listes
                if len(actual_questions) > 3:
                    history_response += f"\nVous avez posé {len(actual_questions)} questions dans cette conversation."

        # Ajouter l'historique en mémoire
        if conversation_id:
            conversation_history[conversation_id].append(f"Réponse : {history_response}")
            
        # IMPORTANT: Sauvegarder la réponse dans la BD
        if conversation_id and current_user:
            save_bot_response(conversation_id, current_user, history_response, current_tokens, message_tokens)
            print(f"✅ Réponse à la question d'historique sauvegardée pour conversation {conversation_id}")
        
        return JSONResponse({"response": history_response})

    # Ajout de la question actuelle à l'historique
    if conversation_id:
        conversation_history[conversation_id].append(f"Question : {user_message}")

    # Récupération du contexte RAG
    context = None
    if not is_history_question and embedding_model:
        context = retrieve_relevant_context(user_message, embedding_model, db.connaissances, k=5)
        if context and conversation_id:
            conversation_history[conversation_id].append(f"Contexte : {context}")

    # Préparation du prompt système
    system_prompt = (
        "Tu es un chatbot spécialisé dans la santé mentale, et plus particulièrement la schizophrénie. "
        "Tu réponds de façon fiable, claire et empathique, en t'appuyant uniquement sur des sources médicales et en français. "
        "IMPORTANT: Fais particulièrement attention aux questions de suivi. Si l'utilisateur pose une question qui ne précise "
        "pas clairement le sujet mais qui fait suite à votre échange précédent, comprends que cette question fait référence "
        "au contexte de la conversation précédente. Par exemple, si l'utilisateur demande 'Comment les traite-t-on?' après "
        "avoir parlé des symptômes positifs de la schizophrénie, ta réponse doit porter spécifiquement sur le traitement "
        "des symptômes positifs, et non sur la schizophrénie en général. IMPORTANT: Vise tes réponses sous forme de Markdown."
        "IMPÉRATIF: Structure tes réponses en Markdown, utilisant **des gras** pour les points importants, "
    "des titres avec ## pour les sections principales, des listes à puces avec * pour énumérer des points, "
    "et > pour les citations importantes. Cela rend ton contenu plus facile à lire et à comprendre."
    
    )

    # Enrichir l prompt avec l'historique et le contexte RAG
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

    # Préparation des messages pour le LLM
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_id and len(conversation_history.get(conversation_id, [])) > 0:
        history = conversation_history[conversation_id]
        
        # Assurer l'alternance user/assistant
        user_messages = []
        bot_messages = []
        
        for i in range(len(history)):
            if i < len(history) and history[i].startswith("Question :"):
                user_text = history[i].replace("Question : ", "")
                user_messages.append(user_text)
                
            if i+1 < len(history) and history[i+1].startswith("Réponse :"):
                bot_text = history[i+1].replace("Réponse : ", "")
                bot_messages.append(bot_text)
        
        # Construire des paires user/assistant
        valid_pairs = min(len(user_messages), len(bot_messages))
        
        for i in range(valid_pairs):
            messages.append({"role": "user", "content": user_messages[i]})
            messages.append({"role": "assistant", "content": bot_messages[i]})
    
    # Ajouter le message actuel
    messages.append({"role": "user", "content": user_message})

    # Fonction génératrice pour le streaming
    async def generate_stream():
        try:
            collected_response = ""
            
            # Signal de début de stream
            yield "data: {\"type\": \"start\"}\n\n"
            
            # Appel à l'API Hugging Face avec streaming
            completion_stream = hf_client.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                stream=True
            )
            chunk_buffer = ""
            chunk_count = 0
            MAX_CHUNKS_BEFORE_SEND = 3  # Envoyer tous les 5 chunks reçus
            # Traiter chaque chunk
            for chunk in completion_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_response += content
                    chunk_buffer += content
                    chunk_count += 1
                    
                    # Envoyer es chunks accumulés périodiquement
                    if chunk_count >= MAX_CHUNKS_BEFORE_SEND or '\n' in content:
                        yield f"data: {json.dumps({'content': chunk_buffer})}\n\n"
                        chunk_buffer = ""
                        chunk_count = 0

            # Envoyer le reste du buffer
            if chunk_buffer:
                yield f"data: {json.dumps({'content': chunk_buffer})}\n\n"
            
            # Ajouter une note si nécessaire
            if collected_response.endswith((".", "!", "?")) == False and len(collected_response) > 500:
                suffix = "\n\n(Note: Ma réponse a été limitée par des contraintes de taille. N'hésitez pas à me demander de poursuivre si vous souhaitez plus d'informations.)"
                collected_response += suffix
                yield f"data: {json.dumps({'content': suffix})}\n\n"
            
            # Sauvegarder la réponse complète dans l'historique en mémoire
            if conversation_id:
                conversation_history[conversation_id].append(f"Réponse : {collected_response}")
                
                if len(conversation_history[conversation_id]) > 50: 
                    conversation_history[conversation_id] = conversation_history[conversation_id][-50:]
            
            # Sauvegarder la réponse dans la BD (sans condition skip_save)
            if conversation_id and current_user:
                save_bot_response(conversation_id, current_user, collected_response, current_tokens, message_tokens)
            
            # Signal de fin de stream
            yield "data: {\"type\": \"end\"}\n\n"
            
        except Exception as e:
            # Gérer les erreurs de streaming
            error_message = str(e)
            print(f"❌ Streaming error: {error_message}")
            
            try:
                # Fallback en mode non-streaming
                fallback = hf_client.text_generation(
                    model="mistralai/Mistral-7B-Instruct-v0.3",
                    prompt=f"<s>[INST] {system_prompt}\n\nQuestion: {user_message} [/INST]",
                    max_new_tokens=512,
                    temperature=0.7
                )
                yield f"data: {json.dumps({'content': fallback})}\n\n"
                
                # Sauvegarder la réponse de fallback dans l'historique
                if conversation_id:
                    conversation_history[conversation_id].append(f"Réponse : {fallback}")
                
                # Sauvegarder la réponse fallback dans la BD
                if conversation_id and current_user:
                    save_bot_response(conversation_id, current_user, fallback, current_tokens, message_tokens)
                    
            except Exception as fallback_error:
                print(f"❌ Erreur de fallback: {str(fallback_error)}")
                error_response = "Je suis désolé, je rencontre actuellement des difficultés techniques. Pourriez-vous reformuler votre question ou réessayer dans quelques instants?"
                yield f"data: {json.dumps({'content': error_response})}\n\n"
                
                # Sauvegarder aussi les messages d'erreur technique
                if conversation_id and current_user:
                    save_bot_response(conversation_id, current_user, error_response, current_tokens, message_tokens)
            
            # Signal de fin de stream
            yield "data: {\"type\": \"end\"}\n\n"
    
    # Retourner une réponse en streaming
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
