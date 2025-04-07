import React from 'react'
import '../login.css'; 


function Signin({toLogin}) {
  return (
    <div className='login'>
        <h1 className='title-1'>Bienvenue sur Medic.ial !</h1>
        <div className="container">
            <div className='container-form'>
                <form action="" className='form'>
                    <h3>INSCRIPTION</h3>
                    <div className='form-container-name'>
                        <div>
                            <p className='form-title'>Prénom</p>
                            <input type='text' className='form-input'/>
                        </div>
                        <div>
                            <p className='form-title'>Nom</p>
                            <input type='text' className='form-input'/>
                        </div>
                    </div>
                    <div className='form-container-input'>
                        <p className='form-title'>Adresse email</p>
                        <input type='mail' className='form-input'/>
                    </div>
                    <div className='form-container-input'>
                        <p className='form-title'>Mot de passe</p>
                        <input type='password' className='form-input'/>
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