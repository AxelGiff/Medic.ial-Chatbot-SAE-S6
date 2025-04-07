import React from 'react';
import '../App.css';

const Panel = ({
  conversations = [],
  setConversations = () => {},
  activeConversationId,
  setActiveConversationId,
  onToggleCollapse,
  isCollapsed,
  onNewChat
}) => {


  const createNewChat = () => {
    onNewChat(); 
  };

const deleteConversation=(conversationId)=>{
  console.log(conversationId)
  setConversations(prev => prev.filter(chat => chat.id !== conversationId));
  setActiveConversationId(null);
  
}

  return (
    <div className={`sidebar-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!isCollapsed && (
          <button className="collapse-button" onClick={onToggleCollapse}>
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
          </button>
        )}
        <button className="new-chat-button" onClick={createNewChat}>
          {!isCollapsed && (
            <span>
              <svg
                viewBox="0 0 512 512"
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                fill="currentColor"
              >
                <path d="M495.6 49.23l-32.82-32.82C451.8 5.471 437.5 0 423.1 0c-14.33 0-28.66 5.469-39.6 16.41L167.5 232.5C159.1 240 154.8 249.5 152.4 259.8L128.3 367.2C126.5 376.1 133.4 384 141.1 384c.916 0 1.852-.0918 2.797-.2813c0 0 74.03-15.71 107.4-23.56c10.1-2.377 19.13-7.459 26.46-14.79l217-217C517.5 106.5 517.4 71.1 495.6 49.23zM461.7 94.4L244.7 311.4C243.6 312.5 242.5 313.1 241.2 313.4c-13.7 3.227-34.65 7.857-54.3 12.14l12.41-55.2C199.6 268.9 200.3 267.5 201.4 266.5l216.1-216.1C419.4 48.41 421.6 48 423.1 48s3.715 .4062 5.65 2.342l32.82 32.83C464.8 86.34 464.8 91.27 461.7 94.4zM424 288c-13.25 0-24 10.75-24 24v128c0 13.23-10.78 24-24 24h-304c-13.22 0-24-10.77-24-24v-304c0-13.23 10.78-24 24-24h144c13.25 0 24-10.75 24-24S229.3 64 216 64L71.1 63.99C32.31 63.99 0 96.29 0 135.1v304C0 479.7 32.31 512 71.1 512h303.1c39.69 0 71.1-32.3 71.1-72L448 312C448 298.8 437.3 288 424 288z" />
              </svg>
            </span>
          )}
        </button>
    
      </div>

      <div className="conversations-list">
        <div class="conversation-today">
          <h6 className="conversation-today-title">Aujourd'hui</h6>
        {conversations.map(chat => (
          <div 
            key={chat.id} 
            className={`conversation-item ${activeConversationId === chat.id ? 'active' : ''}`}
            onClick={() => setActiveConversationId(chat.id)}
          >
           
            {!isCollapsed && (
              <>
               <div className="conversation-icon">
               <span className="material-icons">{chat.time}</span>
             </div>
              <div className="conversation-details">
                
                <div className="conversation-title">{chat.title}</div>
                <div className="conversation-date">{chat.date}</div>
              </div>
              <button className="delete-button" onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(chat.id);
                  }}>


        
              <span>
                <svg width="15px" height="15px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="#ff0000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M10 12V17" stroke="#ff0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M14 12V17" stroke="#ff0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M4 7H20" stroke="#ff0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M6 10V18C6 19.6569 7.34315 21 9 21H15C16.6569 21 18 19.6569 18 18V10" stroke="#ff0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5V7H9V5Z" stroke="#ff0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path> </g></svg>
              </span>
           
            </button>
              </>
            )}
          </div>
        ))}
        </div>
        <div class="conversation-before">
          <h6 className="conversation-before-title">Les 30 derniers jours</h6>
          
           </div>
      </div>

    </div>
  );
};

export default Panel;
