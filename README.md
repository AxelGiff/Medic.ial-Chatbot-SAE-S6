# Projet : Chatbot d'information médicale sur la schizophrénie

# 📄 Mise en contexte
Ce projet a pour objectif de développer une application capable de répondre aux questions des utilisateurs sur des sujets de santé mais plus précisement la schizophrénie 

### L’objectif de ce projet va être de réaliser un Chatbot médical :  
* Modèle spécialisé sur la schizophrénie

### Pour permettre par la suite de :
* Déployer l'application sur internet

## 👥 Membres de l'équipe
* CABO India
* GIFFARD Axel
* HAMSEK Fayçal
* OUCHALLAL Samia

Le chatbot médical sur la schizophrénie est un outil numérique conçu pour fournir des informations claires et accessibles sur cette maladie mentale. Il permet aux utilisateurs de poser des questions et d’obtenir des réponses basées sur des données médicales fiables, concernant les symptômes, les traitements, les causes possibles ou encore le quotidien des personnes atteintes.
Cependant, bien qu’il apporte un soutien informatif utile, ce chatbot ne remplace pas un professionnel de santé. Il ne pose aucun diagnostic, ne propose aucun traitement personnalisé et ne peut pas évaluer la condition d’un utilisateur. Les informations fournies doivent toujours être complétées ou confirmées par l’avis d’un médecin ou d’un psychiatre.

## Demos 

**Déploiement en ligne (Space HuggingFace) :** 
- [Déploiement en ligne](https://huggingface.co/spaces/AxL95/medically))


## Étapes pour lancer en local

### 1. Cloner le projet
```bash
git clone https://github.com/AxelGiff/test_iamedical.git
cd test_iamedical
```

### 2. Lancer le frontend
```bash
npm install
npm start
```

### 3. Lancer le backend
⚠️ **IMPORTANT** : Pour accéder au LLM, vous devez configurer votre token HuggingFace

1. Créez ou modifiez le fichier `.env` **dans le dossier backend :**
   ```
   REACT_APP_HF_TOKEN="Mettre votre token HuggingFace"
   ```

2. Démarrez le serveur :
   ```bash
   cd backend
   python app.py
   ```
   
   Si cette commande ne fonctionne pas, utilisez :
   ```bash
   uvicorn app:app --reload --port 8000
   ```


# Pourquoi réaliser ce projet ? 
<details>
<summary><b>Déroulez pour voir l'ensemble des objectifs : 
</b></summary><br/>
  
- **Exploration et préparation des données** \
  Selection de documents qui seront la base des connaissances.
  Traitement des documents ainsi que des questions pour avoir le plus haut matching possible entre eux.

- **Comprendre et appliquer les techniques propres aux LLM**  
Cela implique d'avoir des notions en mathématiques, science des données, et informatiques pour appliquer des traitements, de savoir et connaître l'ensemble des paramètres et hyperparamètres utilisés, et de savoir optimiser nos modèles.

- **Analyser les biais potentiels** \
Identifier les biais potentiels dans les réponses et les documents fournis au modèle pour ses connaissances.

- **Développer une interface utilisateur** \
Créer une interface simple permettant aux utilisateurs de poser leurs questions via React et CSS.
Cela permettra au cours de nos études de présenter ce projet et que les utilisateurs puissent tester l'application.
</details>

## 🛠️ Langages et outils
- [Python](https://docs.python.org/)
- [Tensorflow](https://www.tensorflow.org/api_docs)
- [Keras](https://keras.io/)
- [Gradio](https://www.gradio.app/docs)
- [HuggingFaces](https://huggingface.co/)
- [Atlas](https://www.mongodb.com/docs/)
- [React](https://react.dev/reference/react)
- [CSS](https://developer.mozilla.org/fr/docs/Web/CSS/Reference)

# 🖼️ Les documents de connaissance
La base de connaissances constitue le centre même du chatbot. Elle a été conçue de façon à fournir des réponses fiables, à partir de documents médicaux sélectionnés avec soin. 
Il y a en tout 14 documents médicaux : 

- **10 relatifs à la schizophrénie qui abordent :**
  - Symptômes
  - Causes
  - Diagnostic
  - Conseils pour les proches
  - Traitements

- **4 relatifs à la médecine générale :**
  - Dictionnaire de termes médicaux
  - Médecine de premier recours
  - Notions anatomiques et physiologiques humaines

## Préparation des documents
Dans un premeir temps, les documents sont découpés en chunk. Pour permettre par la suite leur vectorisation en base grâce au modèle spécialisé dans le langage médical **medical_embedded_v2**. 

**medical_embedded_v2** est un modèle d'apprentissage automatique conçu pour analyser et encoder des données médicales (comme des diagnostics, traitements ou notes cliniques) en vecteurs numériques (embeddings). L’objectif est de représenter ces données de manière compacte et pertinente pour faciliter des tâches comme la classification, la recherche sémantique ou le clustering de patients.


🔍 Objectifs
  - Générer des **embeddings pertinents** à partir de textes médicaux.
  - Améliorer la **précision et la robustesse** des tâches en aval (classification, recherche sémantique, etc.).


⚙️ Caractéristiques
  - Basé sur une architecture **Transformer** (type BERT ou similaire).
  - Fine-tuné sur des jeux de données médicaux pour une meilleure spécialisation.
  - Utilisable pour des tâches telles que :
    - Classification de documents médicaux.
    - Recherche de similarité sémantique.
    - Clustering de patients ou de cas cliniques.


📦 Cas d’utilisation
  - Recommandation de traitements ou diagnostics similaires.
  - Recherche intelligente dans des bases de données de dossiers médicaux.
  - Clustering ou résumé automatique de documents cliniques.

# 🔎 Similatiré entre les questions et les connaissances

Pour que le Chatbot puisse répondre de la manière la plus précise possible aux questions des utilisateurs on utilise un système de matching.
Voici une fonction d’exemple qui utilise un modèle d’embedding et une collection MongoDB pour retrouver les documents les plus similaires à une requête :

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def retrieve_relevant_context(query, embedding_model, mongo_collection, k=3):
    query_embedding = embedding_model.embed_query(query)

    docs = list(mongo_collection.find({}, {"text": 1, "embedding": 1}))
    similarities = [
        cosine_similarity([query_embedding], [doc["embedding"]])[0][0]
        for doc in docs
    ]

    top_k_indices = np.argsort(similarities)[-k:][::-1]
    top_k_docs = [docs[i]["text"] for i in top_k_indices]
    return "\n".join(top_k_docs)

```
**Interface Web**

![image](https://github.com/user-attachments/assets/76324027-3caa-4a3a-ac62-e4662fee475f)

**Backend extraction des documents avec le meilleur matching**

![image](https://github.com/user-attachments/assets/6f63e9ed-1d48-4d9d-ad29-396e1e391e04)
