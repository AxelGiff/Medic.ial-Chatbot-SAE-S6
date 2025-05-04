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
  const updateThreshold = 1; // Toutes les 10 ms
  const updateIntervalRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
    
    if (updateIntervalRef.current) {
      clearInterval(updateIntervalRef.current);
      updateIntervalRef.current = null;
    }
    
   
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
      }, 100); 
    }
    
    // clear l'intervalle
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

      // On ajoute le message de l'utilisateur
      setMessages(prev => [...prev, { 
        sender: 'user', 
        text: message,
        id: userMessageId
      }]);      
   
      const updatedConversationId = await onMessageSent(message);
      
      const streamMessageId = `bot-${Date.now()}`;
    setCurrentStreamId(streamMessageId);
      
      setMessages(prev => {
        const userMessageExists = prev.some(m => m.id === userMessageId);
        
        // Pour rajouter le premier message de l'utilisateur
        const updatedMessages = userMessageExists ? prev : [
          ...prev, 
          { sender: 'user', text: message, id: userMessageId }
        ];
        
        return [...updatedMessages, { 
          sender: 'bot', 
          text: '', 
          id: streamMessageId 
        }];
      });
      
      setIsLoading(false); // Plus de chargement mais streaming
      setIsStreaming(true); // Commencer le streaming
      
      // Faire la requête au backend pour envoyer le prompt et recevoir la réponse
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          message,
          conversation_id: activeConversationId || updatedConversationId,
          skip_save: false 
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();

        // SI LIMITE DE TOKENS ATTEINTE ON ENVOIE UN MESSAGE + On doit obligatoirement créer une nouvelle conversation
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
      
      if (response.headers.get('content-type')?.includes('text/event-stream') && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(5));
                
                if (data.type === 'start') {
                  fullText = '';
                  accumulatedText.current = '';
                } 
                else if (data.type === 'end') {
                  console.log("SSE End received");
                  setIsStreaming(false);
                  setCurrentStreamId(null);
                  setIsLoading(false);
                  
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === streamMessageId 
                        ? { ...msg, sender: 'bot', text: fullText }
                        : msg
                    )
                  );
                  
                  if (typeof refreshConversationList === 'function') {
                    setTimeout(refreshConversationList, 100);
                  }
                  
                  return; 
                }
                else if (data.content) {
                  fullText += data.content;
                  accumulatedText.current += data.content;
                  
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
                    
                    accumulatedText.current = ''; 
                    
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
        
        if (typeof refreshConversationList === 'function') {
          setTimeout(refreshConversationList, 100);
        }
      }
      
    } catch (error) {
      console.error('Erreur lors de l\'envoi/réception du message:', error);
      setIsStreaming(false);
      setCurrentStreamId(null);
      setIsLoading(false);
      
      setMessages(prev => {
        const filteredMessages = prev.filter(m => m.id !== currentStreamId);
        return [...filteredMessages, 
          { sender: 'bot', text: "Désolé, une erreur s'est produite. Veuillez réessayer." }
        ];
      });
    }
  };

  // Créer une nouvelle conversation
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

  // On regarde s'il faut faire du markdown ou pas
  const isMarkdown = (text, sender) => {
    if (sender === 'bot') {
      return true;
    }
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
