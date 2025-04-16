const { MongoClient } = require('mongodb');

exports.handler = async function(event, context) {
  // Vérifier que c'est une requête POST
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  try {
    const data = JSON.parse(event.body);
    const { prenom, nom, email, password } = data;

    // Validation
    if (!prenom || !nom || !email || !password) {
      return { 
        statusCode: 400, 
        body: JSON.stringify({ error: 'Tous les champs sont requis' }) 
      };
    }
    const MONGODB_URI = process.env.MONGODB_URI;
    const DB_NAME = process.env.DB_NAME;

    // Connexion à MongoDB
    const client = new MongoClient(MONGODB_URI);
    await client.connect();
    const db = client.db(DB_NAME);
    const users = db.collection('users');

    // Vérifier si l'email existe déjà
    const existingUser = await users.findOne({ email });
    if (existingUser) {
      return { 
        statusCode: 409, 
        body: JSON.stringify({ error: 'Cet email est déjà utilisé' }) 
      };
    }

    // Insérer l'utilisateur
    const result = await users.insertOne({
      prenom,
      nom,
      email,
      password, // Idéalement, hashez ce mot de passe avant de l'enregistrer
      createdAt: new Date()
    });

    return {
      statusCode: 201,
      body: JSON.stringify({ message: 'Utilisateur créé avec succès', userId: result.insertedId })
    };
  } catch (error) {
    console.error('Erreur:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Erreur serveur' })
    };
  }
};