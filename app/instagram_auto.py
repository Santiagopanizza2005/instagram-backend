import logging
import asyncio
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import json
from datetime import datetime
from app.auto_config import auto_config
from app.auto_auth import auto_auth
from app.clients import AccountManager

class InstagramAutoManager:
    """Manager principal que automatiza todo el proceso de Instagram"""
    
    def __init__(self):
        self.account_manager = AccountManager()
        self.setup_logging()
        
    def setup_logging(self):
        """Configura logging automático"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"instagram_auto_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
        
        logging.info("InstagramAutoManager iniciado")
    
    async def auto_setup_account(self, username: str, password: str) -> Tuple[bool, str]:
        """Setup completo automático de cuenta de Instagram"""
        try:
            logging.info(f"Iniciando setup automático para {username}")
            
            # Paso 1: Configuración automática de IP y dispositivo
            logging.info("Obteniendo configuración automática de IP y dispositivo...")
            config = auto_config.get_auto_config()
            logging.info(f"Configuración obtenida: IP={config['ip']}, DeviceID={config['device_id']}")
            
            # Paso 2: Login automático con reintento inteligente
            logging.info("Intentando login automático...")
            success, client, message = await auto_auth.auto_login(username, password)
            
            if not success:
                error_msg = f"Error en login automático: {message}"
                logging.error(error_msg)
                return (False, error_msg)
            
            # Paso 3: Agregar cuenta al manager
            logging.info("Agregando cuenta al AccountManager...")
            key = self.account_manager._k(username)
            self.account_manager.clients[key] = client
            
            if key not in self.account_manager._tokens:
                self.account_manager._tokens[key] = config['device_id']
            
            # Paso 4: Verificar cuenta
            try:
                account_info = client.account_info()
                logging.info(f"Cuenta verificada exitosamente: {getattr(account_info, 'username', username)}")
            except Exception as e:
                logging.warning(f"No se pudo verificar cuenta info: {e}")
            
            # Paso 5: Guardar configuración final
            self.save_auto_config(username, config)
            
            success_msg = f"Setup automático completado exitosamente para {username}"
            logging.info(success_msg)
            return (True, success_msg)
            
        except Exception as e:
            error_msg = f"Error en setup automático: {str(e)}"
            logging.error(error_msg)
            return (False, error_msg)
    
    async def auto_setup_with_saved_credentials(self) -> Tuple[bool, str]:
        """Setup automático usando credenciales guardadas"""
        try:
            credentials = auto_auth.get_saved_credentials()
            
            if not credentials:
                msg = "No hay credenciales guardadas disponibles"
                logging.warning(msg)
                return (False, msg)
            
            username, password = credentials
            logging.info(f"Iniciando setup automático con credenciales guardadas para {username}")
            
            return await self.auto_setup_account(username, password)
            
        except Exception as e:
            error_msg = f"Error en setup automático con credenciales guardadas: {str(e)}"
            logging.error(error_msg)
            return (False, error_msg)
    
    def save_auto_config(self, username: str, config: Dict[str, Any]) -> bool:
        """Guarda configuración automática final"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            final_config = {
                'username': username,
                'auto_config': config,
                'setup_date': datetime.now().isoformat(),
                'status': 'active'
            }
            
            config_file = config_dir / f"{username}_auto_config.json"
            
            with open(config_file, 'w') as f:
                json.dump(final_config, f, indent=2)
            
            logging.info(f"Configuración automática guardada para {username}")
            return True
            
        except Exception as e:
            logging.error(f"Error guardando configuración final: {e}")
            return False
    
    def get_auto_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema automático"""
        try:
            # Estado de configuración automática
            config = auto_config.get_auto_config()
            
            # Estado de autenticación automática
            auth_status = auto_auth.get_auto_login_status()
            
            # Estado de cuentas en AccountManager
            accounts = self.account_manager.list_accounts()
            
            # Verificar archivos de configuración
            config_dir = Path("config")
            saved_configs = []
            if config_dir.exists():
                for config_file in config_dir.glob("*_auto_config.json"):
                    username = config_file.stem.replace("_auto_config", "")
                    saved_configs.append(username)
            
            status = {
                'auto_config': {
                    'ip': config.get('ip'),
                    'device_id': config.get('device_id'),
                    'user_agent': config.get('user_agent'),
                    'auto_generated': config.get('auto_generated', False)
                },
                'auto_auth': auth_status,
                'accounts': {
                    'total': len(accounts),
                    'usernames': [acc['username'] for acc in accounts],
                    'details': accounts
                },
                'saved_configs': saved_configs,
                'system_status': 'active' if accounts else 'waiting_setup'
            }
            
            return status
            
        except Exception as e:
            logging.error(f"Error obteniendo estado del sistema: {e}")
            return {'error': str(e)}
    
    async def auto_send_message(self, username: str, recipient: str, message: str) -> Tuple[bool, str]:
        """Envío automático de mensaje"""
        try:
            # Verificar que la cuenta esté configurada
            key = self.account_manager._k(username)
            if key not in self.account_manager.clients:
                # Intentar setup automático con credenciales guardadas
                success, setup_msg = await self.auto_setup_with_saved_credentials()
                if not success:
                    return (False, f"Cuenta no configurada y no hay credenciales disponibles: {setup_msg}")
            
            # Enviar mensaje
            success = self.account_manager.send_message(username, recipient, message)
            
            if success:
                return (True, f"Mensaje enviado exitosamente a {recipient}")
            else:
                return (False, "Error al enviar mensaje")
                
        except Exception as e:
            error_msg = f"Error en envío automático: {str(e)}"
            logging.error(error_msg)
            return (False, error_msg)
    
    def reset_all(self) -> bool:
        """Resetea todo el sistema automático"""
        try:
            logging.info("Reseteando sistema automático completo...")
            
            # Limpiar autenticación
            auto_auth.clear_all_data()
            
            # Limpiar configuraciones
            config_dir = Path("config")
            if config_dir.exists():
                for config_file in config_dir.glob("*.json"):
                    config_file.unlink()
            
            # Limpiar logs
            log_dir = Path("logs")
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    log_file.unlink()
            
            logging.info("Sistema automático reseteado completamente")
            return True
            
        except Exception as e:
            logging.error(f"Error reseteando sistema: {e}")
            return False

# Instancia global
instagram_auto = InstagramAutoManager()

# Funciones de conveniencia para uso rápido
async def auto_setup(username: str, password: str) -> Tuple[bool, str]:
    """Setup rápido y automático de cuenta"""
    return await instagram_auto.auto_setup_account(username, password)

async def auto_login_saved() -> Tuple[bool, str]:
    """Login automático con credenciales guardadas"""
    return await instagram_auto.auto_setup_with_saved_credentials()

def get_status() -> Dict[str, Any]:
    """Obtener estado del sistema automático"""
    return instagram_auto.get_auto_status()

async def auto_message(username: str, recipient: str, message: str) -> Tuple[bool, str]:
    """Enviar mensaje automáticamente"""
    return await instagram_auto.auto_send_message(username, recipient, message)