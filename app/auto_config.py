import socket
import requests
import logging
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import secrets

class AutoConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "auto_config.json"
        self.ip_cache = None
        
    def get_public_ip(self) -> Optional[str]:
        """Obtiene la IP pública del usuario automáticamente"""
        try:
            # Intentar múltiples servicios para obtener IP
            services = [
                "https://api.ipify.org",
                "https://ipapi.co/ip/",
                "https://ifconfig.me/ip",
                "https://api.myip.com"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        if self._validate_ip(ip):
                            self.ip_cache = ip
                            logging.info(f"IP detectada automáticamente: {ip}")
                            return ip
                except Exception:
                    continue
                    
            # Si no se puede obtener IP pública, usar IP local
            return self._get_local_ip()
            
        except Exception as e:
            logging.error(f"Error obteniendo IP: {e}")
            return self._get_local_ip()
    
    def _get_local_ip(self) -> str:
        """Obtiene la IP local como fallback"""
        try:
            # Crear un socket para obtener IP local
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            return "127.0.0.1"
    
    def _validate_ip(self, ip: str) -> bool:
        """Valida si una IP es válida"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except Exception:
            return False
    
    def generate_device_id(self, ip: str) -> str:
        """Genera un device ID único basado en la IP"""
        import hashlib
        # Combinar IP con timestamp para hacerlo único
        timestamp = str(int(os.path.getctime(__file__) if os.path.exists(__file__) else 0))
        combined = f"{ip}-{timestamp}-{socket.gethostname()}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def generate_user_agent(self, ip: str) -> str:
        """Genera un User-Agent realista basado en la IP"""
        # User-Agents comunes que funcionan bien con Instagram
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
        # Seleccionar UA basado en IP para consistencia
        import hashlib
        ip_hash = int(hashlib.md5(ip.encode()).hexdigest(), 16)
        return user_agents[ip_hash % len(user_agents)]
    
    def get_auto_config(self) -> Dict[str, Any]:
        """Obtiene configuración automática completa"""
        # Verificar si existe configuración previa
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Verificar si la IP sigue siendo válida
                    if self._validate_ip(config.get('ip', '')):
                        return config
            except Exception:
                pass
        
        # Generar nueva configuración automática
        ip = self.get_public_ip()
        device_id = self.generate_device_id(ip)
        user_agent = self.generate_user_agent(ip)
        
        config = {
            'ip': ip,
            'device_id': device_id,
            'user_agent': user_agent,
            'uuid': secrets.token_hex(16),
            'phone_id': secrets.token_hex(16),
            'adid': secrets.token_hex(16),
            'request_id': secrets.token_hex(16),
            'session_id': secrets.token_hex(16),
            'created_at': int(os.path.getctime(__file__) if os.path.exists(__file__) else 0),
            'auto_generated': True
        }
        
        # Guardar configuración
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info("Configuración automática generada y guardada")
        except Exception as e:
            logging.error(f"Error guardando configuración: {e}")
        
        return config
    
    def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Configura proxy automáticamente si es necesario"""
        # Detectar si estamos en un país que requiere proxy
        try:
            ip = self.get_public_ip()
            # Verificar ubicación aproximada
            response = requests.get(f"https://ipapi.co/{ip}/country/", timeout=3)
            country = response.text.strip() if response.status_code == 200 else None
            
            # Lista de países que podrían necesitar proxy para Instagram
            restricted_countries = ['CN', 'IR', 'KP', 'RU']
            
            if country in restricted_countries:
                # Intentar obtener proxy gratuito (con limitaciones)
                logging.warning(f"Detectado país restringido: {country}, configurando proxy")
                return {
                    'http': 'http://proxy.example.com:8080',  # Placeholder
                    'https': 'https://proxy.example.com:8080'  # Placeholder
                }
        except Exception:
            pass
        
        return None
    
    def setup_instagram_client(self, client) -> None:
        """Configura el cliente de Instagram con configuración automática"""
        config = self.get_auto_config()
        
        # Aplicar configuración al cliente
        client.set_device({
            'device_id': config['device_id'],
            'uuid': config['uuid'],
            'phone_id': config['phone_id'],
            'adid': config['adid'],
            'device_string': config['user_agent']
        })
        
        # Configurar headers
        client.set_user_agent(config['user_agent'])
        
        # Configurar proxy si es necesario
        proxy_config = self.get_proxy_config()
        if proxy_config:
            client.set_proxy(proxy_config)
        
        logging.info(f"Cliente Instagram configurado automáticamente con IP: {config['ip']}")
        return config

# Instancia global
auto_config = AutoConfigManager()