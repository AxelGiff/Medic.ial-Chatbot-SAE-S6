import React from 'react';
import '../avatar.css'; 

export default function Avatar({onClick}) {


  return (
    <div className="avatar-container" onClick={onClick}>
      <div
        className="avatar-image-wrapper"
     
      >
        <img
          className="circular--portrait-img"
          alt="me"
          src={new URL("../../public/logo_schizoprene.png", import.meta.url).href}
        />
      </div>
    </div>
  );
}