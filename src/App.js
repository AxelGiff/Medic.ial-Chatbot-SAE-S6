import React, { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import Panel from './components/Panel';

function App() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([
    { id: 1, title: "Premier diagnostic", date: "12 Mar" },
    { id: 2, title: "Question sur les symptômes", date: "11 Mar" },
    { id: 3, title: "Consultation générale", date: "10 Mar" }
  ]);
  const [activeConversationId, setActiveConversationId] = useState(null);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  const handleMessageSent = (message) => {
  
    if (!activeConversationId) {
      const newChat = { 
        id: Date.now(), 
        title: message.length > 15 ? message.substring(0, 15) + "..." : message,   
        date: new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
        time: new Date().toLocaleTimeString('fr-FR', { hour: 'numeric', minute: 'numeric' }) 

      };
      setConversations([newChat, ...conversations]);
      setActiveConversationId(newChat.id);
    }
  };

  return (
    <div className={`App ${isCollapsed ? 'panel-collapsed' : ''}`}>
      <Panel 
        conversations={conversations}
        setConversations={setConversations}
        activeConversationId={activeConversationId}
        setActiveConversationId={setActiveConversationId}
        onNewChat={handleNewChat} 
        onToggleCollapse={toggleCollapse} 
        isCollapsed={isCollapsed} 
      />
      
      <div className="main-content">
        {isCollapsed && (
          <button className="collapse-button-main" onClick={toggleCollapse}>
            <span className="material-icons">
              <svg
                fill="#FFFF"
                width="20"
                height="20"
                viewBox="0 0 32 32"
                xmlns="http://www.w3.org/2000/svg"
              >
                <defs>
                  <style>{`.cls-1{fill:none;}`}</style>
                </defs>
                <title>open-panel--solid--left</title>
                <path d="M28,4H4A2,2,0,0,0,2,6V26a2,2,0,0,0,2,2H28a2,2,0,0,0,2-2V6A2,2,0,0,0,28,4Zm0,22H12V6H28Z" />
                <rect
                  id="_Transparent_Rectangle_"
                  data-name="<Transparent Rectangle>"
                  className="cls-1"
                  width="20"
                  height="20"
                />
              </svg>
            </span>
          </button>
        )}
        
        <ChatInterface
          messages={messages}
          setMessages={setMessages}
          onMessageSent={handleMessageSent}
        />
      </div>
    </div>
  );
}

export default App;