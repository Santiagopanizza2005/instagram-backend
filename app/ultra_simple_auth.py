import logging
import asyncio
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta
from instagrapi import Client
from app.auto_config import auto_config

class UltraSimpleAuth:
    """Sistema de autenticación ultra-simplificado - sin cookies manuales"""
    
    def __init__(self):
        self.auth_dir = Path("auth")
        self.auth_dir.mkdir(exist_ok=True)
        self.credentials_file = self.auth_dir / "simple_credentials.json"
        self.max_retries = 3
        self.retry_delay = 5
        
    def save_credentials(self, username: str, password: str) -> bool:
        """Guarda credenciales de forma ultra-simple"""
        try:
            credentials = {
                username: {
                    'password': password,  # En producción: encriptar
                    'created_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat()
                }
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            logging.info(f"✅ Credenciales guardadas automáticamente para {username}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error guardando credenciales: {e}")
            return False
    
    def get_saved_credentials(self) -> Optional[Tuple[str, str]]:
        """Obtiene credenciales guardadas"""
        try:
            if not self.credentials_file.exists():
                return None
            
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            
            if not credentials:
                return None
            
            # Obtener el primer usuario (normalmente solo hay uno)
            username = list(credentials.keys())[0]
            password = credentials[username]['password']
            
            return (username, password)
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo credenciales: {e}")
            return None
    
    async def ultra_simple_login(self, username: str, password: str) -> Tuple[bool, Optional[Client], str]:
        """Login ultra-simple sin cookies manuales"""
        client = Client()
        
        # Configurar cliente automáticamente
        auto_config.setup_instagram_client(client)
        
        logging.info(f"🔄 Intentando login para {username}...")
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    logging.info(f"🔄 Reintento {attempt + 1}/{self.max_retries}")
                    await asyncio.sleep(self.retry_delay * attempt)
                
                # Login simple - solo usuario y contraseña
                client.login(username, password)
                
                # Verificar que el login fue exitoso
                client.account_info()
                
                # Guardar credenciales para uso futuro
                self.save_credentials(username, password)
                
                logging.info(f"✅ Login exitoso para {username}")
                return (True, client, "Login exitoso")
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"❌ Error en intento {attempt + 1}: {error_msg}")
                
                if attempt == self.max_retries - 1:
                    return (False, None, f"Login fallido después de {self.max_retries} intentos")
        
        return (False, None, "Login fallido")
    
    async def auto_login_with_saved(self) -> Tuple[bool, Optional[Client], str]:
        """Login automático con credenciales guardadas"""
        credentials = self.get_saved_credentials()
        
        if not credentials:
            return (False, None, "No hay credenciales guardadas")
        
        username, password = credentials
        logging.info(f"🔐 Usando credenciales guardadas para {username}")
        
        return await self.ultra_simple_login(username, password)
    
    def clear_credentials(self) -> bool:
        """Limpia credenciales guardadas"""
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
                logging.info("✅ Credenciales limpiadas")
                return True
            return True
        except Exception as e:
            logging.error(f"❌ Error limpiando credenciales: {e}")
            return False

# Instancia global
ultra_simple_auth = UltraSimpleAuth()