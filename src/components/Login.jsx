import React from 'react'
import '../login.css'; 


const Login = ({toSignin}) => {
  return (
    <div className='login'>
        <h1 className='title-1'>Te voilà de retour sur Medic.ial !</h1>
        <div className="container">
            <div className='container-form'>
                <form action="" className='form'>
                    <h3>CONNEXION</h3>
                    <div className='form-container-input'>
                        <p className='form-title'>Adresse email</p>
                        <input type='mail' className='form-input'/>
                    </div>
                    <div className='form-container-input'>
                        <p className='form-title'>Mot de passe</p>
                        <input type='password' className='form-input'/>
                    </div>
                    <div className='form-container-submit'>
                        <button type="submit">Connexion</button>
                        <p>Mot de passe oublié?</p>
                    </div>
                </form>
            </div>
        </div>
        <p className='title-2'>Pas encore de compte ? <span onClick={toSignin}>S'inscrire</span></p>
    </div>
  )
}

export default Login