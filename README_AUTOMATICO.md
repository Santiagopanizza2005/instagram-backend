# 🤖 Instagram API Automática 100%

Sistema completamente automático para gestionar cuentas de Instagram sin configuración manual. Todo funciona con la IP real del usuario y se configura automáticamente.

## 🚀 Características Principales

- **📍 Detección automática de IP**: Detecta tu IP pública automáticamente
- **🔧 Configuración automática**: Configura device ID, user-agent y todos los parámetros necesarios
- **🔐 Login automático**: Inicia sesión automáticamente con guardado de credenciales
- **💾 Sesiones persistentes**: Guarda y reutiliza sesiones automáticamente
- **🔄 Reintento inteligente**: Reintenta automáticamente en caso de fallos
- **🌐 Proxy automático**: Detecta si necesitas proxy basado en tu ubicación
- **📊 Logging completo**: Registra todo automáticamente para debugging

## ⚡ Uso Rápido (100% Automático)

### 1. Setup Completo Automático

```python
import asyncio
from app.instagram_auto import auto_setup

# Setup completamente automático - ¡No necesitas configurar nada!
username = "tu_usuario"
password = "tu_contraseña"

async def main():
    success, message = await auto_setup(username, password)
    print(f"Resultado: {message}")

asyncio.run(main())
```

### 2. Login con Credenciales Guardadas

```python
import asyncio
from app.instagram_auto import auto_login_saved

# Login automático con credenciales guardadas
async def main():
    success, message = await auto_login_saved()
    print(f"Resultado: {message}")

asyncio.run(main())
```

### 3. Enviar Mensaje Automáticamente

```python
import asyncio
from app.instagram_auto import auto_message

async def main():
    success, message = await auto_message("tu_usuario", "destinatario", "Hola mundo!")
    print(f"Resultado: {message}")

asyncio.run(main())
```

## 🎯 Demo Interactiva

Ejecuta la demo interactiva para ver todo en acción:

```bash
python demo_auto.py
```

La demo te mostrará:
- ✅ Detección automática de tu IP
- ✅ Configuración automática de dispositivo
- ✅ Login automático con guardado de sesión
- ✅ Envío automático de mensajes

## 📁 Estructura del Sistema

```
api IG/
├── app/
│   ├── clients.py          # Gestor de cuentas modificado
│   ├── auto_config.py      # Configuración automática de IP/dispositivo
│   ├── auto_auth.py        # Autenticación automática
│   └── instagram_auto.py   # Manager principal
├── config/                 # Configuraciones automáticas
│   ├── auto_config.json    # Config base automática
│   └── *_auto_config.json  # Configs por usuario
├── auth/                   # Credenciales y sesiones
│   ├── auto_sessions.json  # Sesiones guardadas
│   └── auto_credentials.json # Credenciales guardadas
├── logs/                   # Logs automáticos
└── demo_auto.py           # Demo interactiva
```

## 🔧 Cómo Funciona (Automático)

### 1. Detección de IP (Automática)
```python
# Tu IP se detecta automáticamente
ip = auto_config.get_public_ip()  # Ej: "190.123.45.67"
```

### 2. Configuración de Dispositivo (Automática)
```python
# Device ID único basado en tu IP
device_id = auto_config.generate_device_id(ip)
# Ej: "a1b2c3d4e5f6g7h8"

# User-Agent realista basado en tu IP
user_agent = auto_config.generate_user_agent(ip)
# Ej: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
```

### 3. Login Automático
```python
# Intenta con sesión guardada primero
saved_session = auto_auth.get_saved_session(username)

# Si no hay sesión válida, hace login automático
success, client, message = await auto_auth.auto_login(username, password)
```

### 4. Todo Junto (Automático)
```python
# ¡Una sola línea hace TODO!
success, message = await auto_setup(username, password)
```

## 🌍 Detección de Proxy (Automática)

El sistema detecta automáticamente si estás en un país restringido:

```python
# Detecta ubicación automáticamente
if country in ['CN', 'IR', 'KP', 'RU']:
    # Configura proxy automáticamente
    proxy_config = auto_config.get_proxy_config()
```

## 📊 Monitoreo Automático

Obtén estado del sistema en cualquier momento:

```python
status = get_status()
print(f"IP: {status['auto_config']['ip']}")
print(f"Cuentas activas: {status['accounts']['total']}")
print(f"Estado: {status['system_status']}")
```

## 🛡️ Seguridad Automática

- Credenciales guardadas con encriptación básica
- Sesiones con expiración automática (30 días)
- Device IDs únicos por IP
- User-Agents realistas y rotativos
- Logs automáticos para auditoría

## 🔄 Reintento Inteligente

El sistema reintenta automáticamente:
- Hasta 3 intentos en caso de fallo
- Delay entre intentos (5s, 10s, 15s)
- Cambio de endpoints si es necesario
- Fallback a IP local si falla IP pública

## 📝 Ejemplos Completos

### Ejemplo 1: Setup y Envío Automático
```python
import asyncio
from app.instagram_auto import auto_setup, auto_message

async def ejemplo_completo():
    # Setup automático
    success, msg = await auto_setup("mi_usuario", "mi_contraseña")
    
    if success:
        # Enviar mensaje automáticamente
        success2, msg2 = await auto_message("mi_usuario", "amigo", "Hola!")
        print("Mensaje enviado automáticamente!" if success2 else f"Error: {msg2}")

asyncio.run(ejemplo_completo())
```

### Ejemplo 2: Verificación de Estado
```python
from app.instagram_auto import get_status

# Ver estado del sistema automáticamente
status = get_status()
print(f"Sistema automático: {'Activo' if status['system_status'] == 'active' else 'Inactivo'}")
print(f"IP detectada: {status['auto_config']['ip']}")
print(f"Cuentas configuradas: {status['accounts']['total']}")
```

## 🚨 Solución de Problemas

### Si el login falla automáticamente:
1. Verifica tus credenciales
2. Ejecuta `python demo_auto.py` para debugging
3. Revisa los logs en `logs/`
4. El sistema reintentará automáticamente

### Si la IP no se detecta:
1. Usa IP local automáticamente
2. Verifica tu conexión a internet
3. El sistema usará fallback automático

## 🎉 ¡Todo es Automático!

- ✅ No necesitas configurar IP manualmente
- ✅ No necesitas configurar device ID
- ✅ No necesitas configurar user-agent
- ✅ No necesitas guardar sesiones manualmente
- ✅ No necesitas manejar reintentos
- ✅ No necesitas configurar proxy
- ✅ Todo se hace automáticamente con TU IP real

¡Simplemente ejecuta y el sistema hace TODO por ti! 🤖