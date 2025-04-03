import React from 'react';
import '../avatar.css'; 

export default function Avatar() {


  return (
    <div className="avatar-container">
      <div
        className="avatar-image-wrapper"
     
      >
        <img
          className="circular--portrait-img"
          alt="me"
          src={new URL("../../public/emojipouce.png", import.meta.url).href}
        />
      </div>
    </div>
  );
}