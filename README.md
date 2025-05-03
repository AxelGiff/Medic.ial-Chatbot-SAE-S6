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



