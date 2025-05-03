import React, { useState } from 'react'
import '../login.css';

const Login = ({toSignin, onLoginSuccess}) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        
        try {
            const response = await fetch('http://localhost:8000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',  
                body: JSON.stringify({
                    email,
                    password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('userName', data.username);
                localStorage.setItem('userId', data.user_id);
                localStorage.setItem('userRole', data.role); 

               
                if (onLoginSuccess) {
                    onLoginSuccess();
                }
                
            } else {
                setError(data.detail || 'Identifiants incorrects');
            }
        } catch (err) {
            setError('Erreur de connexion au serveur');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className='login'>
            <h1 className='title-1'>Te voilà de retour sur Medic.ial !</h1>
            <div className="container">
                <div className='container-form'>
                    <form onSubmit={handleSubmit} className='form'>
                        <h3>CONNEXION</h3>
                        
                        {error && <div className="error-message">{error}</div>}
                        
                        <div className='form-container-input'>
                            <p className='form-title'>Adresse email</p>
                            <input 
                                type='email' 
                                className='form-input'
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className='form-container-input'>
                            <p className='form-title'>Mot de passe</p>
                            <input 
                                type='password' 
                                className='form-input'
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                        <div className='form-container-submit'>
                            <button 
                                type="submit" 
                                disabled={isLoading}
                            >
                                {isLoading ? 'Connexion...' : 'Connexion'}
                            </button>
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
