import logging
import asyncio
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import json
from datetime import datetime
from app.ultra_simple_auth import ultra_simple_auth
from app.auto_config import auto_config
from app.clients import AccountManager

class InstagramUltraAuto:
    """Sistema Instagram 100% automático - sin cookies, sin configuración"""
    
    def __init__(self):
        self.account_manager = AccountManager()
        self.setup_auto_logging()
        
    def setup_auto_logging(self):
        """Configura logging automático"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 🤖 %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"ultra_auto_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
        
        logging.info("🚀 InstagramUltraAuto iniciado - Sistema 100% automático")
    
    async def ultra_setup(self, username: str, password: str) -> Tuple[bool, str]:
        """Setup ultra-automático - solo usuario y contraseña"""
        try:
            logging.info(f"🔄 Iniciando setup ultra-automático para {username}")
            
            # Paso 1: Configuración automática de IP y dispositivo
            logging.info("📍 Detectando IP automáticamente...")
            config = auto_config.get_auto_config()
            logging.info(f"✅ IP detectada: {config['ip']}")
            logging.info(f"✅ Device ID generado: {config['device_id']}")
            
            # Paso 2: Login ultra-simple - sin cookies manuales
            logging.info("🔐 Iniciando login automático...")
            success, client, message = await ultra_simple_auth.ultra_simple_login(username, password)
            
            if not success:
                error_msg = f"❌ Login fallido: {message}"
                logging.error(error_msg)
                return (False, error_msg)
            
            # Paso 3: Agregar al manager automáticamente
            logging.info("📊 Agregando cuenta al manager...")
            key = self.account_manager._k(username)
            self.account_manager.clients[key] = client
            
            if key not in self.account_manager._tokens:
                self.account_manager._tokens[key] = config['device_id']
            
            # Paso 4: Verificar cuenta automáticamente
            try:
                account_info = client.account_info()
                logging.info(f"✅ Cuenta verificada: {getattr(account_info, 'username', username)}")
            except Exception as e:
                logging.warning(f"⚠️  No se pudo verificar info de cuenta: {e}")
            
            # Paso 5: Guardar configuración final
            self.save_ultra_config(username, config)
            
            success_msg = f"✅ Setup ultra-automático completado para {username}"
            logging.info(success_msg)
            return (True, success_msg)
            
        except Exception as e:
            error_msg = f"❌ Error en setup ultra-automático: {str(e)}"
            logging.error(error_msg)
            return (False, error_msg)
    
    async def ultra_login_saved(self) -> Tuple[bool, str]:
        """Login automático con credenciales guardadas"""
        try:
            logging.info("🔐 Intentando login automático con credenciales guardadas...")
            
            success, client, message = await ultra_simple_auth.auto_login_with_saved()
            
            if not success:
                return (False, f"❌ {message}")
            
            # Obtener username de las credenciales
            credentials = ultra_simple_auth.get_saved_credentials()
            if not credentials:
                return (False, "❌ No se pudieron obtener credenciales")
            
            username, _ = credentials
            
            # Agregar al manager
            key = self.account_manager._k(username)
            self.account_manager.clients[key] = client
            
            if key not in self.account_manager._tokens:
                config = auto_config.get_auto_config()
                self.account_manager._tokens[key] = config['device_id']
            
            logging.info(f"✅ Login automático exitoso para {username}")
            return (True, f"✅ Login automático exitoso para {username}")
            
        except Exception as e:
            error_msg = f"❌ Error en login automático: {str(e)}"
            logging.error(error_msg)
            return (False, error_msg)
    
    def save_ultra_config(self, username: str, config: Dict[str, Any]) -> bool:
        """Guarda configuración ultra-automática"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            ultra_config = {
                'username': username,
                'setup_type': 'ultra_auto',
                'ip': config['ip'],
                'device_id': config['device_id'],
                'user_agent': config['user_agent'],
                'setup_date': datetime.now().isoformat(),
                'status': 'active',
                'no_manual_cookies': True
            }
            
            config_file = config_dir / f"{username}_ultra.json"
            
            with open(config_file, 'w') as f:
                json.dump(ultra_config, f, indent=2)
            
            logging.info(f"✅ Configuración ultra guardada para {username}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error guardando configuración ultra: {e}")
            return False
    
    async def ultra_send_message(self, username: str, recipient: str, message: str) -> Tuple[bool, str]:
        """Envío ultra-automático de mensajes"""
        try:
            # Verificar si la cuenta está activa
            key = self.account_manager._k(username)
            if key not in self.account_manager.clients:
                # Intentar login automático
                success, login_msg = await self.ultra_login_saved()
                if not success:
                    return (False, f"❌ Cuenta no activa y login fallido: {login_msg}")
            
            # Enviar mensaje automáticamente
            success = self.account_manager.send_message(username, recipient, message)
            
            if success:
                logging.info(f"✅ Mensaje enviado a {recipient}")
                return (True, f"✅ Mensaje enviado exitosamente a {recipient}")
            else:
                logging.error(f"❌ Error enviando mensaje a {recipient}")
                return (False, "❌ Error al enviar mensaje")
                
        except Exception as e:
            error_msg = f"❌ Error en envío ultra-automático: {str(e)}"
            logging.error(error_msg)
            return (False, error_msg)
    
    def get_ultra_status(self) -> Dict[str, Any]:
        """Obtiene estado ultra-automático del sistema"""
        try:
            # Configuración automática
            config = auto_config.get_auto_config()
            
            # Credenciales guardadas
            credentials = ultra_simple_auth.get_saved_credentials()
            
            # Cuentas activas
            accounts = self.account_manager.list_accounts()
            
            # Configuraciones ultra
            config_dir = Path("config")
            ultra_configs = []
            if config_dir.exists():
                for config_file in config_dir.glob("*_ultra.json"):
                    username = config_file.stem.replace("_ultra", "")
                    ultra_configs.append(username)
            
            status = {
                'system': {
                    'type': 'ultra_auto',
                    'status': 'active' if accounts else 'waiting_setup',
                    'no_manual_cookies': True
                },
                'network': {
                    'ip': config['ip'],
                    'device_id': config['device_id'],
                    'user_agent': config['user_agent']
                },
                'credentials': {
                    'has_saved': credentials is not None,
                    'username': credentials[0] if credentials else None
                },
                'accounts': {
                    'total': len(accounts),
                    'usernames': [acc['username'] for acc in accounts]
                },
                'ultra_configs': ultra_configs
            }
            
            return status
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo estado ultra: {e}")
            return {'error': str(e)}
    
    def reset_ultra_system(self) -> bool:
        """Resetea todo el sistema ultra-automático"""
        try:
            logging.info("🔄 Resetando sistema ultra-automático...")
            
            # Limpiar credenciales
            ultra_simple_auth.clear_credentials()
            
            # Limpiar configuraciones
            config_dir = Path("config")
            if config_dir.exists():
                for config_file in config_dir.glob("*_ultra.json"):
                    config_file.unlink()
            
            # Limpiar logs
            log_dir = Path("logs")
            if log_dir.exists():
                for log_file in log_dir.glob("ultra_auto_*.log"):
                    log_file.unlink()
            
            logging.info("✅ Sistema ultra-automático reseteado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error reseteando sistema ultra: {e}")
            return False

# Instancia global
instagram_ultra = InstagramUltraAuto()

# Funciones de conveniencia ultra-simples
async def ultra_setup(username: str, password: str) -> Tuple[bool, str]:
    """Setup ultra-automático - solo usuario y contraseña"""
    return await instagram_ultra.ultra_setup(username, password)

async def ultra_login() -> Tuple[bool, str]:
    """Login ultra-automático con credenciales guardadas"""
    return await instagram_ultra.ultra_login_saved()

async def ultra_message(username: str, recipient: str, message: str) -> Tuple[bool, str]:
    """Envío ultra-automático de mensajes"""
    return await instagram_ultra.ultra_send_message(username, recipient, message)

def ultra_status() -> Dict[str, Any]:
    """Estado ultra-automático del sistema"""
    return instagram_ultra.get_ultra_status()