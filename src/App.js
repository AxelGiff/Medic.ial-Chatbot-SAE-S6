import React, { useState, useEffect } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import Panel from './components/Panel';
import Login from './components/Login';
import Signin from './components/Signin';
import AdminPanel from './components/AdminPanel';
function App() {
  // L'ensemble des états pour controler toutes les pages
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userName, setUserName] = useState('');
  const [page, setPage] = useState("login"); 
  const [userRole, setUserRole] = useState('');

// Store les roles et le nom dans un stockage local
useEffect(() => {
  const storedUserName = localStorage.getItem('userName');
  const storedUserRole = localStorage.getItem('userRole');

  if (storedUserName) {
    setUserName(storedUserName);
    setUserRole(storedUserRole); 
    setIsAuthenticated(true);
    
    setPage("chat");
    
    fetchConversations();
    
    console.log("Role chargé depuis localStorage:", storedUserRole);
  }
}, []);

  // va chercher la route /api/conversations pour récupérer les conversations
  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/conversations', {
        credentials: 'include', 
      });
      
      if (response.ok) {
        const data = await response.json();
        const formattedConversations = data.conversations.map(conv => ({
          id: conv._id,
          title: conv.title,
          date: conv.date,
          time: conv.time,
          lastMessage: conv.last_message
        }));
        setConversations(formattedConversations);
      } else {
        console.error('Erreur lors de la récupération des conversations');
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };
  const refreshConversationList = async () => {
    await fetchConversations(); 
  };
  // Va récupérer les messages d'une conversation
  const loadConversationMessages = async (conversationId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/conversations/${conversationId}/messages`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        const formattedMessages = data.messages.map(msg => ({
          sender: msg.sender,
          text: msg.text,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des messages:', error);
    }
  };
  
  useEffect(() => {
    if (activeConversationId && isAuthenticated) {
      loadConversationMessages(activeConversationId);
    }
  }, [activeConversationId, isAuthenticated]);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  // Au clic d'une nouvelle conversation on reset les messages
  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  const handleMessageSent = async (message) => {
    let conversationId = activeConversationId;
    
    if (!conversationId) {
      const newChatData = { 
        title: message.length > 15 ? message.substring(0, 15) + "..." : message,
        date: new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
        time: new Date().toLocaleTimeString('fr-FR', { hour: 'numeric', minute: 'numeric' }),
        message: message
      };
      // Va POST et la conversation, et les messages de la conversation
      try {
        const response = await fetch('http://localhost:8000/api/conversations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify(newChatData)
        });
        
        if (response.ok) {
          const data = await response.json();
          conversationId = data.conversation_id; 
          
          const newChat = {
            id: conversationId,
            title: newChatData.title,
            date: newChatData.date,
            time: newChatData.time
          };
          
          setConversations([newChat, ...conversations]);
          setActiveConversationId(conversationId);
          
          await fetch(`http://localhost:8000/api/conversations/${conversationId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              sender: 'user',
              text: message
            })
          });
        }
      } catch (error) {
        console.error('Erreur lors de la création de la conversation:', error);
        return;
      }
    } else {
      
      try {
        await fetch(`http://localhost:8000/api/conversations/${conversationId}/messages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            sender: 'user',
            text: message
          })
        });
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement du message:', error);
      }
    }
    
    return conversationId;
  };
  
  const saveBotResponse = async (conversationId, botResponse, shouldSave = false) => {
    if (!conversationId || !shouldSave) return;
    
    try {
      await fetch(`http://localhost:8000/api/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          sender: 'bot',
          text: botResponse
        })
      });
    } catch (error) {
      console.error('Erreur lors de l\'enregistrement de la réponse du bot:', error);
    }
  };

  const handleLoginSuccess = () => {
    const storedUserName = localStorage.getItem('userName');
    const storedUserRole = localStorage.getItem('userRole');

    setUserName(storedUserName);
    setUserRole(storedUserRole);
    setIsAuthenticated(true);

    setPage(storedUserRole === "Administrateur" ? "Administrateur" : "chat");

    
    fetchConversations();
  };
  // Hanndle pour se déconnecter
  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
      
      localStorage.removeItem('userName');
      localStorage.removeItem('userId');
      localStorage.removeItem('userRole'); 

      setIsAuthenticated(false);
      setUserName('');
      setUserRole(''); 

      setConversations([]);
      setMessages([]);
      setActiveConversationId(null);
      setPage("login");
    } catch (error) {
      console.error("Erreur lors de la déconnexion:", error);
    }
  };

  return (
    <div className={`App ${isCollapsed ? 'panel-collapsed' : ''}`}>
    
     
      {page === "chat" && (
        <Panel 
          conversations={conversations}
          setConversations={setConversations}
          activeConversationId={activeConversationId}
          setActiveConversationId={setActiveConversationId}
          onNewChat={handleNewChat} 
          onToggleCollapse={toggleCollapse} 
          isCollapsed={isCollapsed} 
          userName={userName}
          onLogout={handleLogout}
          setPage={setPage}
          userRole={userRole}
          
        />
      )}
       {page === "Administrateur" && (
      <AdminPanel 
        isCollapsed={isCollapsed}
        onToggleCollapse={toggleCollapse}
        userName={userName}
        onLogout={handleLogout}
        setPage={setPage} 
      />
    )}
      
      <div className="main-content">
        {isCollapsed && page === "chat" && (
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

        {page === "chat" && 
          <ChatInterface
          
            messages={messages}
            setMessages={setMessages}
            onMessageSent={handleMessageSent}
            activeConversationId={activeConversationId}
            saveBotResponse={saveBotResponse}
            userName={userName}
            toLogin={handleLogout} 
            onNewChat={handleNewChat}
            refreshConversationList={refreshConversationList} 

          />
        }
        {page === "login" && <Login toSignin={() => setPage("signin")} onLoginSuccess={handleLoginSuccess}/>}
        {page === "signin" && <Signin toLogin={() => setPage("login")}/>}
      </div>
    </div>
  );
}

export default App;
