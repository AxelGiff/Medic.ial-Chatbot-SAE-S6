import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Avatar from './Avatar.jsx';
import '../App.css';

const ChatInterface = ({ 
  messages = [], 
  setMessages = () => {}, 
  onMessageSent = () => {}, 
  activeConversationId,
  saveBotResponse, 
  toLogin, 
  onNewChat = () => {},
  refreshConversationList = () => {} 
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [tokenLimitReached, setTokenLimitReached] = useState(false);
  const [hasInteractionStarted, setHasInteractionStarted] = useState(false);
  const [currentStreamId, setCurrentStreamId] = useState(null);
  
  // Pour optimiser les performances du streaming
  const accumulatedText = useRef('');
  const updateThreshold = 1; 
  const updateIntervalRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
    
    // Nettoyer l'intervalle précédent si existant
    if (updateIntervalRef.current) {
      clearInterval(updateIntervalRef.current);
      updateIntervalRef.current = null;
    }
    
    // Créer un nouvel intervalle si en streaming
    if (isStreaming && currentStreamId) {
      updateIntervalRef.current = setInterval(() => {
        if (accumulatedText.current.length > 0) {
          setMessages(prev => {
            return prev.map(msg => 
              msg.id === currentStreamId 
                ? { ...msg, text: msg.text + accumulatedText.current } 
                : msg
            );
          });
          accumulatedText.current = '';
        }
      }, 100); // Mise à jour toutes les 100ms pour plus de fluidité
    }
    
    // Nettoyage lors du démontage
    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
    };
  }, [isStreaming, currentStreamId, messages]);
  const sendMessage = async (message) => {
    try {
      setHasInteractionStarted(true);
      setIsLoading(true);
      const userMessageId = `user-${Date.now()}`;

      // Ajouter le message de l'utilisateur
      setMessages(prev => [...prev, { 
        sender: 'user', 
        text: message,
        id: userMessageId
      }]);      
      // Envoyer le message au backend
      const updatedConversationId = await onMessageSent(message);
      
      // Créer un ID unique pour le message en streaming
      const streamMessageId = `bot-${Date.now()}`;
    setCurrentStreamId(streamMessageId);
      
      // Ajouter un message bot vide pour le streaming
      setMessages(prev => {
        // Vérifier si le message utilisateur existe déjà
        const userMessageExists = prev.some(m => m.id === userMessageId);
        
        // Si pour une raison quelconque le message utilisateur a disparu, le rajouter
        const updatedMessages = userMessageExists ? prev : [
          ...prev, 
          { sender: 'user', text: message, id: userMessageId }
        ];
        
        // Ajouter le message bot de streaming
        return [...updatedMessages, { 
          sender: 'bot', 
          text: '', 
          id: streamMessageId 
        }];
      });
      
      setIsLoading(false); // Plus de chargement mais streaming
      setIsStreaming(true); // Commencer le streaming
      
      // Faire la requête au backend
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          message,
          conversation_id: activeConversationId || updatedConversationId,
          skip_save: false // Le backend gère la sauvegarde
        }),
      });
      
      // Gestion des erreurs HTTP
      if (!response.ok) {
        const errorData = await response.json();
        
        if (errorData.error === 'token_limit_exceeded') {
          setIsStreaming(false);
          setCurrentStreamId(null);
          setTokenLimitReached(true);
          
          setMessages(prev => [...prev.filter(m => m.id !== streamMessageId), { 
            sender: 'bot', 
            text: "⚠️ **Limite de taille de conversation atteinte**\n\nCette conversation est devenue trop longue. Pour continuer à discuter, veuillez créer une nouvelle conversation." 
          }]);
          
          return;
        }
        
        throw new Error(`Chat API error ${response.status}`);
      }
      
      // Traiter la réponse en streaming si disponible
      if (response.headers.get('content-type')?.includes('text/event-stream') && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          // Décoder et traiter les données
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(5));
                
                if (data.type === 'start') {
                  console.log("Début du streaming");
                  fullText = '';
                  accumulatedText.current = '';
                } 
                else if (data.type === 'end') {
                  console.log("SSE End received");
                  setIsStreaming(false);
                  setCurrentStreamId(null);
                  setIsLoading(false);
                  
                  // Mise à jour finale
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === streamMessageId 
                        ? { ...msg, sender: 'bot', text: fullText }
                        : msg
                    )
                  );
                  
                  // Rafraîchir la liste des conversations
                  if (typeof refreshConversationList === 'function') {
                    setTimeout(refreshConversationList, 100);
                  }
                  
                  return; // Sortir de la boucle une fois terminé
                }
                else if (data.content) {
                  // Ajouter le contenu du chunk
                  fullText += data.content;
                  accumulatedText.current += data.content;
                  
                  // Mise à jour moins fréquente de l'interface
                  if (accumulatedText.current.length >= updateThreshold || data.content.includes('\n')) {
                    setMessages(prev => {
                      const userMsg = prev.find(m => m.sender === 'user' && m.text === message);
                      const botMsg = prev.find(m => m.id === streamMessageId);
                      
                      const updatedMessages = userMsg ? prev : [
                        ...prev, 
                        { sender: 'user', text: message, id: `user-${Date.now()}` }
                      ];
                      
                      if (botMsg) {
                        return updatedMessages.map(msg => 
                          msg.id === streamMessageId ? { ...msg, text: fullText } : msg
                        );
                      } else {
                        return [...updatedMessages, { sender: 'bot', text: fullText, id: streamMessageId }];
                      }
                    });
                    
                    accumulatedText.current = ''; // Réinitialiser l'accumulateur
                    
                    // Faire défiler vers le bas
                    requestAnimationFrame(() => {
                      scrollToBottom();
                    });
                  }
                }
                else if (data.type === 'error') {
                  console.error("SSE Error received:", data.error);
                  setIsStreaming(false);
                  setCurrentStreamId(null);
                  setIsLoading(false);
                  
                  // Remplacer par un message d'erreur
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === streamMessageId 
                        ? { sender: 'bot', text: "Désolé, une erreur s'est produite." }
                        : msg
                    )
                  );
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e, line);
              }
            }
          }
        }
      } 
      else {
        // Fallback pour les réponses non-streaming
        console.log("Received non-streaming response.");
        const responseData = await response.json();
        setIsStreaming(false);
        setCurrentStreamId(null);
        setIsLoading(false);
        
        setMessages(prev => 
          prev.map(msg => 
            msg.id === streamMessageId 
              ? { sender: 'bot', text: responseData.response, id: streamMessageId }
              : msg
          )
        );
        
        // Rafraîchir la liste des conversations
        if (typeof refreshConversationList === 'function') {
          setTimeout(refreshConversationList, 100);
        }
      }
      
    } catch (error) {
      console.error('Erreur lors de l\'envoi/réception du message:', error);
      setIsStreaming(false);
      setCurrentStreamId(null);
      setIsLoading(false);
      
      // Afficher l'erreur
      setMessages(prev => {
        const filteredMessages = prev.filter(m => m.id !== currentStreamId);
        return [...filteredMessages, 
          { sender: 'bot', text: "Désolé, une erreur s'est produite. Veuillez réessayer." }
        ];
      });
    }
  };

  const handleCreateNewConversation = () => {
    onNewChat();
    setTokenLimitReached(false);
    setHasInteractionStarted(false);
  };
  
  useEffect(() => {
    if (activeConversationId === null && messages.length === 0) {
      setHasInteractionStarted(false);
    }
  }, [activeConversationId, messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const txt = inputMessage.trim();
    if (!txt) return;
    sendMessage(txt);
    setInputMessage('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const isMarkdown = (text, sender) => {
    // Forcer le rendu Markdown pour TOUS les messages du bot
    if (sender === 'bot') {
      return true;
    }
    // Pour les messages utilisateur, vérifier la présence de syntaxe Markdown
    return /(?:\*\*|__|##|\*|_|`|>|\d+\.\s|\-\s|\[.*\]\(.*\))/.test(text);
  };
  
  
  return (
    <div className="chat-container">
      {messages.length === 0 && !hasInteractionStarted ? (
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
          {messages.map((msg, index) => {
  const isActiveStreaming = isStreaming && msg.id === currentStreamId;
  
  return (
    <div key={msg.id || index} className={`message ${msg.sender}`}>
      <div className={`message-content ${isActiveStreaming ? 'streaming-message' : ''}`}>
        {isMarkdown(msg.text, msg.sender) ? 
          <ReactMarkdown>{msg.text}</ReactMarkdown> : 
          <span>{msg.text}</span>
        }
        {isActiveStreaming && (
          <span className="typing-indicator">▌</span>
        )}
      </div>
    </div>
  );
})}
            
            {tokenLimitReached && (
              <div className="token-limit-warning">
                <button 
                  className="new-conversation-button"
                  onClick={handleCreateNewConversation}
                >
                  Démarrer une nouvelle conversation
                </button>
              </div>
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
          <div className="input-container">
            <form onSubmit={handleSubmit} className="input-form">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={tokenLimitReached ? "Créez une nouvelle conversation pour continuer..." : "Tapez votre message ici..."}
                disabled={isLoading || tokenLimitReached}
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
              <button type="submit" disabled={isLoading || !inputMessage.trim() || tokenLimitReached}>
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
