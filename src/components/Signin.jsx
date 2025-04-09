import React, { useState } from 'react'
import '../login.css'; 


function Signin({toLogin}) {

    const [formData,setFormData]=useState({
        prenom:'',
        nom:'',
        email:'',
        password_hash:'',
    });
    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
      };
    
      const handleSubmit = async (e) => {
        e.preventDefault();
        try {
          const res = await fetch("http://127.0.0.1:8000/register", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
          });
    
          const data = await res.json();
          if (res.ok) {
            alert("Inscription réussie !");
            toLogin();  
          } else {
            alert(data.detail || "Erreur à l'inscription");
          }
        } catch (error) {
          console.error("Erreur réseau :", error);
        }
      };

  return (
    <div className='login'>
        <h1 className='title-1'>Bienvenue sur Medic.ial !</h1>
        <div className="container">
            <div className='container-form'>
                <form action="" className='form' onSubmit={handleSubmit}>
                    <h3>INSCRIPTION</h3>
                    <div className='form-container-name'>
                        <div>
                            <p className='form-title'>Prénom</p>
                            <input type='text' name="prenom" onChange={handleChange} value={formData.prenom} className='form-input'/>
                        </div>
                        <div>
                            <p className='form-title'>Nom</p>
                            <input type='text' name="nom" onChange={handleChange} value={formData.nom} className='form-input'/>
                        </div>
                    </div>
                    <div className='form-container-input'>
                        <p className='form-title'>Adresse email</p>
                        <input type='mail' name="email" onChange={handleChange} value={formData.email} className='form-input'/>
                    </div>
                    <div className='form-container-input'>
                        <p className='form-title'>Mot de passe</p>
                        <input type='password' name="password_hash" onChange={handleChange} value={formData.password_hash} className='form-input'/>
                    </div>
                    <div className='form-container-submit'>
                        <button type="submit">Inscription</button>
                    </div>
                </form>
            </div>
        </div>
        <p className='title-2'>Déjà un compte ? <span onClick={toLogin}>Se connecter</span></p>
    </div>
  )
}

export default Signin