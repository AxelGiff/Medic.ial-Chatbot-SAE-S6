import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Fonction simple de détection de Markdown
  const isMarkdown = (text) => {
    // On vérifie la présence de quelques symboles courants du Markdown
    return /[#*_>`-]/.test(text);
  };

  // Fonction pour envoyer un message au backend
  const sendMessage = async (message) => {
    try {
      setIsLoading(true);
      
    
      
      // Envoi de la requête à l'API Gradio
      const response = await axios.post('https://dd704091d27b57de3c.gradio.live/gradio_api/run/predict', {
        data: [message, null],
        fn_index: 0
      });
      
      // Récupération de la réponse dans le tableau renvoyé par Gradio
      const botResponse = response.data.data[0];
      
      // Mettre à jour l'état avec la réponse
      setMessages(prevMessages => [
        ...prevMessages, 
        { sender: 'user', text: message },
        { sender: 'bot', text: botResponse }
      ]);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      setIsLoading(false);
      
      // Gestion de l'erreur dans l'interface
      setMessages(prevMessages => [
        ...prevMessages,
        { sender: 'user', text: message },
        { sender: 'bot', text: "Désolé, une erreur s'est produite. Veuillez réessayer." }
      ]);
    }
  };

  // Gérer la soumission du formulaire
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;
    
    sendMessage(inputMessage);
    setInputMessage('');
  };

  // Faire défiler automatiquement vers le bas quand de nouveaux messages arrivent
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Mon Chatbot IA Médicale</h2>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <p>Bonjour ! Comment puis-je vous aider aujourd'hui ?</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div className="message-content">
                {isMarkdown(msg.text) ? (
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                ) : (
                  msg.text
                )}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message bot">
            <div className="message-content loading">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Tapez votre message ici..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || inputMessage.trim() === ''}>
          Envoyer
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
