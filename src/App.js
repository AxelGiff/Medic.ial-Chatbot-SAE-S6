import React, { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import Panel from './components/Panel';

function App() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`App ${isCollapsed ? 'panel-collapsed' : ''}`}>
      <Panel onToggleCollapse={toggleCollapse} isCollapsed={isCollapsed} />
      
      <div className="main-content">
        {/* 
          Si le panel est replié (isCollapsed === true),
          on affiche un bouton "menu" en haut à gauche 
          pour le rouvrir.
        */}
        {isCollapsed && (
          <button className="collapse-button-main" onClick={toggleCollapse}>
            <span className="material-icons">menu</span>
          </button>
        )}
        
        <ChatInterface />
      </div>
    </div>
  );
}

export default App;
