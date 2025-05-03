import React, { useState, useEffect } from 'react';
import './AdminPanel.css';

function AdminPanel({ isCollapsed, onToggleCollapse, userName, onLogout,setPage }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadData, setUploadData] = useState({
    title: '',
    tags: ''
  });
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);
  
  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/admin/knowledge', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents);
      } else {
        const errorData = await response.json();
        setError(`Erreur: ${errorData.detail || 'Impossible de charger les documents'}`);
      }
    } catch (err) {
      setError(`Erreur: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setUploadData({
      ...uploadData,
      [name]: value
    });
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setUploadStatus('Veuillez sélectionner un fichier PDF');
      return;
    }

    setUploadStatus('Téléchargement en cours...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', uploadData.title || selectedFile.name);
    formData.append('tags', uploadData.tags);

    try {
      const response = await fetch('http://localhost:8000/api/admin/knowledge/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus('Document téléchargé avec succès!');
        setUploadData({ title: '', tags: '' });
        setSelectedFile(null);
      } else {
        setUploadStatus(`Erreur: ${data.detail || 'Échec du téléchargement'}`);
      }
    } catch (err) {
      setUploadStatus(`Erreur: ${err.message}`);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce document?')) {
      return;
    }

    try {
        const response = await fetch(`http://localhost:8000/api/admin/knowledge/${docId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        setDocuments(documents.filter(doc => doc.id !== docId));
        setUploadStatus('Document supprimé avec succès!');
        setTimeout(() => setUploadStatus(null), 3000); 
      } else {
        const data = await response.json();
        setError(`Erreur: ${data.detail || 'Échec de la suppression'}`);
      }
    } catch (err) {
      setError(`Erreur: ${err.message}`);
    }
  };

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h1>Panneau d'administration</h1>
        <div className="admin-user-info">
          <span>Connecté en tant que: {userName}</span>
          <button onClick={() => setPage("chat")} className="back-btn">
            Retour au chat
          </button>
          <button onClick={onLogout} className="logout-btn">Déconnexion</button>
        </div>
      </div>

      <div className="admin-content">
        <div className="admin-section">
          <h2>Ajouter un document PDF</h2>
          <form onSubmit={handleUpload} className="upload-form">
            <div className="form-group">
              <label>Titre (optionnel):</label>
              <input
                type="text"
                name="title"
                value={uploadData.title}
                onChange={handleInputChange}
                placeholder="Titre du document"
              />
            </div>
            
            <div className="form-group">
              <label>Tags (séparés par des virgules):</label>
              <input
                type="text"
                name="tags"
                value={uploadData.tags}
                onChange={handleInputChange}
                placeholder="schizophrénie, traitement, symptômes, etc."
              />
            </div>
            
            <div className="form-group">
              <label>Fichier PDF:</label>
              <input 
                type="file" 
                accept=".pdf" 
                onChange={handleFileChange} 
              />
            </div>
            
            <button type="submit" className="upload-btn">
              Télécharger le document
            </button>
            
            {uploadStatus && (
              <div className={`upload-status ${uploadStatus.includes('Erreur') ? 'error' : 'success'}`}>
                {uploadStatus}
              </div>
            )}
          </form>
          
<div className="admin-section">
  <h2>Documents disponibles</h2>
  {isLoading ? (
    <p>Chargement...</p>
  ) : error ? (
    <p className="error">{error}</p>
  ) : documents.length === 0 ? (
    <p>Aucun document trouvé.</p>
  ) : (
    <table className="documents-table">
      <thead>
        <tr>
          <th>Titre</th>
          <th>Tags</th>
          <th>Date d'ajout</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {documents.map(doc => (
          <tr key={doc.id}>
            <td>{doc.title}</td>
            <td>{doc.tags.join(', ')}</td>
            <td>{new Date(doc.date).toLocaleDateString()}</td>
            <td>
              <button onClick={() => handleDelete(doc.id)} className="delete-btn">
                Supprimer
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )}
</div>
        </div>

        
      </div>
    </div>
  );
}

export default AdminPanel;
