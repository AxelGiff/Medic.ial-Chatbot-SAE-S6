import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Avatar from './Avatar.jsx';
import '../App.css';

const ChatInterface = ({ messages = [], setMessages = () => {}, onMessageSent = () => {}, activeConversationId,
saveBotResponse, toLogin }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(scrollToBottom, [messages]);

  const sendMessage = async (message) => {
    try {
      setIsLoading(true);
      
      // Ajouter le message utilisateur à l'interface
      setMessages(prev => [...prev, { sender: 'user', text: message }]);
      
      // IMPORTANT: Obtenir l'ID de conversation mis à jour (nouvelle ou existante)
      const updatedConversationId = await onMessageSent(message);
      
      // Appel à l'API de chat
      const chatRes = await fetch('http://localhost:7860/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message }),
      });
      
      if (!chatRes.ok) throw new Error(`Chat API error ${chatRes.status}`);
      
      const { response: botResponse } = await chatRes.json();
      
      // Ajouter la réponse du bot à l'interface
      setMessages(prev => [...prev, { sender: 'bot', text: botResponse }]);
      
      // Utiliser l'ID de conversation mis à jour
      if (updatedConversationId) {
        saveBotResponse(updatedConversationId, botResponse);
      } else if (activeConversationId) {
        saveBotResponse(activeConversationId, botResponse);
      }
      
    } catch (error) {
      console.error('Erreur:', error);
      setMessages(prev => [...prev, 
        { sender: 'user', text: message },
        { sender: 'bot', text: "Désolé, une erreur s'est produite. Veuillez réessayer." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const txt = inputMessage.trim();
    if (!txt) return;
    sendMessage(txt);
    setInputMessage('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const isMarkdown = (text) => /[#*_>`-]/.test(text);

  return (
    <div className="chat-container">
      {messages.length === 0 ? (
        <>
          <div className="chat-header">
            <h2 className="chat-title">Medic.ial</h2>
            <Avatar onClick={toLogin} />
          </div>
          <div className="no-messages-view">
            <div className="welcome-content">
              <div className="welcome-message">
                <p>Bonjour ! Comment puis-je vous aider aujourd'hui ? 🧑‍⚕️</p>
              </div>
              <div className="input-container centered">
                <form onSubmit={handleSubmit} className="input-form">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Posez une question..."
                    disabled={isLoading}
                    rows="1"
                    ref={textareaRef}
                    className="input-textarea"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                    onInput={(e) => {
                      e.target.style.height = 'auto';
                      e.target.style.height = `${e.target.scrollHeight}px`;
                    }}
                  />
                  <button type="submit" disabled={isLoading || !inputMessage.trim()}>
                    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3">
                      <path d="M120-160v-240l320-80-320-80v-240l760 320-760 320Z"/>
                    </svg>
                  </button>
                </form>
              </div>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="chat-header">
            <Avatar onClick={toLogin} />
            <h2 className="chat-title">Medic.ial</h2>
          </div>
          <div className="messages-container">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender}`}>
                <div className="message-content">
                  {isMarkdown(msg.text) ? <ReactMarkdown>{msg.text}</ReactMarkdown> : msg.text}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message bot">
                <div className="message-content loading">
                  <span>.</span><span>.</span><span>.</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="input-container">
            <form onSubmit={handleSubmit} className="input-form">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Tapez votre message ici..."
                disabled={isLoading}
                rows="1"
                ref={textareaRef}
                className="input-textarea"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = `${e.target.scrollHeight}px`;
                }}
              />
              <button type="submit" disabled={isLoading || !inputMessage.trim()}>
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3">
                  <path d="M120-160v-240l320-80-320-80v-240l760 320-760 320Z"/>
                </svg>
              </button>
            </form>
            <figcaption className="disclaimer-text">
              Medic.ial est sujet à faire des erreurs. Vérifiez les informations fournies.
            </figcaption>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatInterface;
