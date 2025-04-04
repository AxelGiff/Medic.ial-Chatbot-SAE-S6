import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import Avatar from './Avatar.jsx';
import '../App.css';

const ChatInterface = ({ messages = [], setMessages = () => {}, onMessageSent = () => {} }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null); 


  const isMarkdown = (text) => /[#*_>`-]/.test(text);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (message) => {
    try {
      setIsLoading(true);
      
      onMessageSent(message);
      
      const response = await axios.post('https://15af0837fca124cf6d.gradio.live/gradio_api/run/predict', {
        data: [message, null],
        fn_index: 0
      });
      const botResponse = response.data.data[0];
      setMessages(prev => [
        ...prev,
        { sender: 'user', text: message },
        { sender: 'bot', text: botResponse }
      ]);
      setIsLoading(false);
    } catch (error) {
      console.error("Erreur:", error);
      setIsLoading(false);
      setMessages(prev => [
        ...prev,
        { sender: 'user', text: message },
        { sender: 'bot', text: "Désolé, une erreur s'est produite. Veuillez réessayer. 👍" }
      ]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;
    sendMessage(inputMessage);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setInputMessage('');
    
  };

  // Le reste du composant reste inchangé
  return (
    <div className="chat-container">
      {messages.length === 0 ? (
       <>
       <div className="chat-header">
         <h2 className="chat-title">Medic.ial</h2>
         <Avatar />
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
      className="input-textarea"
      onKeyDown={(e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault(); 
          handleSubmit(e); 
        }
      }}
      onInput={(e) => {
        e.target.style.height = "auto"; // Réinitialise la hauteur
        e.target.style.height = `${e.target.scrollHeight}px`; // Ajuste à la hauteur du contenu
      }}
    />
               <button type="submit" style={{background:"none"}} disabled={isLoading || inputMessage.trim() === ''}>
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
            <Avatar />
            <h2 className="chat-title">Medic.ial</h2>
          </div>
          <div className="messages-container">
  {messages.map((msg, index) => (
    <div key={index} className={`message ${msg.sender}`}>
      <div className="message-content">
        {isMarkdown(msg.text) ? (
          <ReactMarkdown>{msg.text}</ReactMarkdown>
        ) : (
          msg.text
        )}
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
                onChange={(e) => setInputMessage(e.target.value)  
                }
                placeholder="Tapez votre message ici..."
                disabled={isLoading}
                rows="1" 
                ref={textareaRef}
                className="input-textarea"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault(); 
                    handleSubmit(e); 
                  }
                }}
                onInput={(e) => {
                  e.target.style.height = "auto"; 
                  e.target.style.height = `${e.target.scrollHeight}px`; 
                }}
    />
              <button type="submit" disabled={isLoading || inputMessage.trim() === ''}>
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3">
                  <path d="M120-160v-240l320-80-320-80v-240l760 320-760 320Z"/>
                </svg>
              </button>
            </form>
            <figcaption className="disclaimer-text">Medic.ial est sujet à faire des erreurs. Vérifiez les informations fournies.</figcaption>
          </div>
        </>
      )}
    </div>
  );
};
/*const UserList = () => {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch('/.netlify/functions/get_users');
        const data = await response.json();
        setUsers(data);
      } catch (error) {
        console.error('An error occurred while fetching users:', error);
      }
    };

    fetchUsers();
  }, []);

  return (
    <div>
      <h1>User List</h1>
      <ul>
        {users.map((user, index) => (
          <li key={index}>{user[1]} - {user[2]}</li>
        ))}
      </ul>
    </div>
  );
};*/

export default ChatInterface;
