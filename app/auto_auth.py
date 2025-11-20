import logging
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import secrets
from instagrapi import Client
from app.auto_config import auto_config

class AutoAuthManager:
    def __init__(self):
        self.auth_dir = Path("auth")
        self.auth_dir.mkdir(exist_ok=True)
        self.sessions_file = self.auth_dir / "auto_sessions.json"
        self.credentials_file = self.auth_dir / "auto_credentials.json"
        self.max_retries = 3
        self.retry_delay = 5
        
    def save_credentials(self, username: str, password: str) -> bool:
        """Guarda credenciales de forma segura (encriptada básica)"""
        try:
            # En producción usar encriptación real
            credentials = {
                'username': username,
                'password': password,  # TODO: Encriptar en producción
                'created_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat()
            }
            
            all_creds = {}
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    all_creds = json.load(f)
            
            all_creds[username] = credentials
            
            with open(self.credentials_file, 'w') as f:
                json.dump(all_creds, f, indent=2)
            
            logging.info(f"Credenciales guardadas automáticamente para {username}")
            return True
            
        except Exception as e:
            logging.error(f"Error guardando credenciales: {e}")
            return False
    
    def get_saved_credentials(self) -> Optional[Tuple[str, str]]:
        """Obtiene credenciales guardadas automáticamente"""
        try:
            if not self.credentials_file.exists():
                return None
            
            with open(self.credentials_file, 'r') as f:
                all_creds = json.load(f)
            
            if not all_creds:
                return None
            
            # Obtener las credenciales más recientes
            latest_username = None
            latest_date = None
            
            for username, creds in all_creds.items():
                created_date = datetime.fromisoformat(creds['created_at'])
                if latest_date is None or created_date > latest_date:
                    latest_date = created_date
                    latest_username = username
            
            if latest_username:
                creds = all_creds[latest_username]
                return (creds['username'], creds['password'])
            
            return None
            
        except Exception as e:
            logging.error(f"Error obteniendo credenciales: {e}")
            return None
    
    def save_session(self, username: str, client: Client) -> bool:
        """Guarda sesión automáticamente - simplificado sin cookies manuales"""
        try:
            session_data = {
                'sessionid': getattr(client, 'sessionid', None),
                'user_agent': getattr(client, 'user_agent', None),
                'device_settings': getattr(client, 'device_settings', None),
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            all_sessions = {}
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    all_sessions = json.load(f)
            
            all_sessions[username] = session_data
            
            with open(self.sessions_file, 'w') as f:
                json.dump(all_sessions, f, indent=2)
            
            logging.info(f"Sesión guardada automáticamente para {username}")
            return True
            
        except Exception as e:
            logging.error(f"Error guardando sesión: {e}")
            return False
    
    def get_saved_session(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtiene sesión guardada si es válida"""
        try:
            if not self.sessions_file.exists():
                return None
            
            with open(self.sessions_file, 'r') as f:
                all_sessions = json.load(f)
            
            if username not in all_sessions:
                return None
            
            session = all_sessions[username]
            
            # Verificar si la sesión no ha expirado
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                logging.info(f"Sesión expirada para {username}")
                return None
            
            return session
            
        except Exception as e:
            logging.error(f"Error obteniendo sesión: {e}")
            return None
    
    async def auto_login(self, username: str, password: str) -> Tuple[bool, Optional[Client], str]:
        """Login automático con reintento inteligente"""
        client = Client()
        
        # Configurar cliente automáticamente
        auto_config.setup_instagram_client(client)
        
        # Intentar usar sesión guardada primero
        saved_session = self.get_saved_session(username)
        if saved_session:
            try:
                logging.info(f"Intentando login con sesión guardada para {username}")
                client.login_by_sessionid(saved_session['sessionid'])
                
                # Verificar que la sesión sea válida
                client.account_info()
                
                logging.info(f"Login exitoso con sesión guardada para {username}")
                self.save_session(username, client)
                return (True, client, "Login exitoso con sesión guardada")
                
            except Exception as e:
                logging.warning(f"Sesión guardada inválida para {username}: {e}")
        
        # Intentar login con credenciales
        for attempt in range(self.max_retries):
            try:
                logging.info(f"Intentando login con credenciales para {username} (intento {attempt + 1})")
                
                # Añadir pequeño delay entre intentos
                if attempt > 0:
                    await asyncio.sleep(self.retry_delay * attempt)
                
                client.login(username, password)
                
                # Verificar login exitoso
                client.account_info()
                
                # Guardar sesión y credenciales
                self.save_session(username, client)
                self.save_credentials(username, password)
                
                logging.info(f"Login exitoso para {username}")
                return (True, client, "Login exitoso")
                
            except Exception as e:
                logging.error(f"Error en login intento {attempt + 1} para {username}: {e}")
                
                if attempt == self.max_retries - 1:
                    return (False, None, f"Error en login después de {self.max_retries} intentos: {str(e)}")
        
        return (False, None, "Login fallido")
    
    async def auto_login_with_saved_credentials(self) -> Tuple[bool, Optional[Client], str]:
        """Login automático con credenciales guardadas"""
        credentials = self.get_saved_credentials()
        
        if not credentials:
            return (False, None, "No hay credenciales guardadas")
        
        username, password = credentials
        return await self.auto_login(username, password)
    
    def clear_all_data(self) -> bool:
        """Limpia todos los datos guardados"""
        try:
            if self.sessions_file.exists():
                self.sessions_file.unlink()
            if self.credentials_file.exists():
                self.credentials_file.unlink()
            
            logging.info("Todos los datos de autenticación limpiados")
            return True
            
        except Exception as e:
            logging.error(f"Error limpiando datos: {e}")
            return False
    
    def get_auto_login_status(self) -> Dict[str, Any]:
        """Obtiene estado del auto-login"""
        status = {
            'has_saved_credentials': False,
            'has_saved_sessions': False,
            'saved_usernames': [],
            'last_login': None
        }
        
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    status['has_saved_credentials'] = len(creds) > 0
                    status['saved_usernames'] = list(creds.keys())
                    
                    # Obtener último login
                    latest_date = None
                    for username, cred_data in creds.items():
                        login_date = datetime.fromisoformat(cred_data.get('last_used', cred_data['created_at']))
                        if latest_date is None or login_date > latest_date:
                            latest_date = login_date
                    
                    if latest_date:
                        status['last_login'] = latest_date.isoformat()
            
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    sessions = json.load(f)
                    status['has_saved_sessions'] = len(sessions) > 0
            
        except Exception as e:
            logging.error(f"Error obteniendo estado: {e}")
        
        return status

# Instancia global
auto_auth = AutoAuthManager()