import React, { useState } from 'react';
import '../App.css';

const Panel = ({ onToggleCollapse, isCollapsed }) => {
  const [conversations, setConversations] = useState([
    { id: 1, title: "Premier diagnostic", date: "12 Mar" },
    { id: 2, title: "Question sur les symptômes", date: "11 Mar" },
    { id: 3, title: "Consultation générale", date: "10 Mar" }
  ]);

  const createNewChat = () => {
    const newChat = { 
      id: conversations.length + 1, 
      title: "Nouvelle conversation", 
      date: new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
    };
    setConversations([newChat, ...conversations]);
  };

  return (
    <div className={`sidebar-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-button" onClick={createNewChat}>
          <span className="material-icons">add</span>
          {!isCollapsed && <span>Nouvelle conversation</span>}
        </button>
        {!isCollapsed && (
          <button className="collapse-button" onClick={onToggleCollapse}>
            <span className="material-icons">menu</span>
          </button>
        )}
      </div>

      <div className="conversations-list">
        {conversations.map(chat => (
          <div key={chat.id} className="conversation-item">
            <div className="conversation-icon">
              <span className="material-icons">chat</span>
            </div>
            {!isCollapsed && (
              <div className="conversation-details">
                <div className="conversation-title">{chat.title}</div>
                <div className="conversation-date">{chat.date}</div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        {!isCollapsed && (
          <div className="user-info">
            <div className="user-avatar">
              <span className="material-icons">account_circle</span>
            </div>
            <div className="user-name">Utilisateur</div>
          </div>
        )}
        <div className="footer-actions">
          {!isCollapsed && <button className="settings-button">
            <span className="material-icons">settings</span>
          </button>}
        </div>
      </div>
    </div>
  );
};

export default Panel;
