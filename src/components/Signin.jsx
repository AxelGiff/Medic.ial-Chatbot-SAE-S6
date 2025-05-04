import React, { useState } from 'react'
import '../login.css';

function Signin({toLogin}) {
    const [formData, setFormData] = useState({
        prenom: '',
        nom: '',
        email: '',
        password: '', 
    });

    // Va enregistrer dans formData les identifiants
    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
    };
    
    // Va POST les identifiants pour se créer un compte
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch("http://localhost:8000/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });

            if (res.ok) {
                const data = await res.json();
                console.log(data);
                toLogin();
            } else {
                const errorData = await res.json().catch(() => ({}));
                alert(errorData.detail || "Erreur d'inscription");
            }
        } catch (error) {
            console.error("Erreur lors de l'inscription", error);
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
                            <input type='email' name="email" onChange={handleChange} value={formData.email} className='form-input'/>
                        </div>
                        <div className='form-container-input'>
                            <p className='form-title'>Mot de passe</p>
                            <input type='password' name="password" onChange={handleChange} value={formData.password} className='form-input'/>
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
