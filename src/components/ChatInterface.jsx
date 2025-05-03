import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Avatar from './Avatar.jsx';
import '../App.css';

const ChatInterface = ({ messages = [], setMessages = () => {}, onMessageSent = () => {}, activeConversationId,
saveBotResponse, toLogin,  onCreateNewConversation = () => {},onNewChat = () => {},refreshConversationList = () => {}
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [fullResponse, setFullResponse] = useState('');
  const [tokenLimitReached, setTokenLimitReached] = useState(false);
  const [hasInteractionStarted, setHasInteractionStarted] = useState(false);

 

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(scrollToBottom, [messages]);


 
  const streamResponse = (response) => {
    setIsStreaming(true);
    setFullResponse(response);
    setStreamingText('');
    
    let streamMessageId = Date.now().toString();
    
    setMessages(prev => [...prev, { 
      sender: 'bot-streaming', 
      text: '', 
      id: streamMessageId 
    }]);
    
    const totalCharacters = response.length;
    let charCount = 0;
    
    const streamInterval = setInterval(() => {
      if (charCount < totalCharacters) {
        charCount += 5;
        const fragment = response.substring(0, charCount);
        
        setMessages(prev => 
          prev.map(msg => 
            msg.id === streamMessageId ? { ...msg, text: fragment } : msg
          )
        );
        
        setStreamingText(fragment);
      } else {
        clearInterval(streamInterval);
        setIsStreaming(false);
        
        setMessages(prev => 
          prev.map(msg => 
            msg.id === streamMessageId 
              ? { sender: 'bot', text: response, id: streamMessageId } 
              : msg
          )
        );
      }
    }, 30);
    
    return () => clearInterval(streamInterval);
  };
  const sendMessage = async (message) => {
    try {
      setHasInteractionStarted(true);
      setIsLoading(true);
      
      setMessages(prev => [...prev, { sender: 'user', text: message }]);
     
      const updatedConversationId = await onMessageSent(message);
      
      const chatRes = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          message,
          conversation_id: activeConversationId,
          skip_save: true  
        }),
      });
      
      const responseData = await chatRes.json();
      
      if (responseData.error === 'token_limit_exceeded') {
        setIsLoading(false);
        setTokenLimitReached(true);
        
        setMessages(prev => [...prev, { 
          sender: 'bot', 
          text: "⚠️ **Limite de taille de conversation atteinte**\n\nCette conversation est devenue trop longue. Pour continuer à discuter, veuillez créer une nouvelle conversation." 
        }]);
        
        return;
      }
      
      if (!chatRes.ok) throw new Error(`Chat API error ${chatRes.status}`);
      
      const { response: botResponse } = responseData;
      
      setIsLoading(false);
      
      streamResponse(botResponse);
 
      if (activeConversationId && typeof refreshConversationList === 'function') {
        refreshConversationList();
      }
      
      if (updatedConversationId) {
        saveBotResponse(updatedConversationId, botResponse, true);  
      } else if (activeConversationId) {
        saveBotResponse(activeConversationId, botResponse, true); 
      }
      
    } catch (error) {
      console.error('Erreur:', error);
      setIsLoading(false);
      setMessages(prev => [...prev, 
        { sender: 'bot', text: "Désolé, une erreur s'est produite. Veuillez réessayer." }
      ]);
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

  const isMarkdown = (text) => /[#*_>`-]/.test(text);

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
              if (msg.sender === 'bot-streaming') return null;
              
              return (
                <div key={index} className={`message ${msg.sender}`}>
                  <div className="message-content">
                    {isMarkdown(msg.text) ? <ReactMarkdown>{msg.text}</ReactMarkdown> : msg.text}
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
              {isStreaming && (
              <div className="message bot">
                <div className="message-content streaming-message">
                  {isMarkdown(streamingText) ? <ReactMarkdown>{streamingText}</ReactMarkdown> : streamingText}
                </div>
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
