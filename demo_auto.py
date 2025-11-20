#!/usr/bin/env python3
"""
Instagram API Automática - Script de Demostración

Este script demuestra el uso completo del sistema automático de Instagram.
Todo se ejecuta automáticamente sin configuración manual.

Características:
- Detección automática de IP del usuario
- Configuración automática de dispositivo y user-agent
- Login automático con guardado de sesión
- Reintento inteligente en caso de fallos
- Gestión automática de credenciales y sesiones
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from app.instagram_auto import (
    instagram_auto, 
    auto_setup, 
    auto_login_saved, 
    get_status,
    auto_message
)

async def demo_auto_setup():
    """Demostración de setup automático completo"""
    print("🚀 Iniciando demostración de Instagram API Automática")
    print("=" * 60)
    
    # Obtener estado actual
    print("📊 Obteniendo estado del sistema...")
    status = get_status()
    print(f"🌐 IP detectada: {status['auto_config']['ip']}")
    print(f"📱 Device ID: {status['auto_config']['device_id']}")
    print(f"🔑 Credenciales guardadas: {status['auto_auth']['has_saved_credentials']}")
    print(f"📊 Cuentas configuradas: {status['accounts']['total']}")
    print()
    
    # Opción 1: Setup con credenciales nuevas
    print("🔐 Opción 1: Setup con credenciales nuevas")
    print("Ingrese sus credenciales de Instagram (se guardarán automáticamente):")
    
    username = input("Usuario de Instagram: ").strip()
    if username:
        password = input("Contraseña: ").strip()
        
        print(f"\n🔄 Configurando cuenta automáticamente para {username}...")
        success, message = await auto_setup(username, password)
        
        if success:
            print(f"✅ {message}")
            print("✅ Configuración automática completada exitosamente")
            print("✅ Sesión guardada automáticamente")
            print("✅ Credenciales encriptadas y guardadas")
        else:
            print(f"❌ Error: {message}")
            return False
    else:
        # Opción 2: Login con credenciales guardadas
        print("\n🔐 Opción 2: Login con credenciales guardadas")
        print("🔄 Intentando login automático con credenciales guardadas...")
        
        success, message = await auto_login_saved()
        
        if success:
            print(f"✅ {message}")
            print("✅ Login automático exitoso")
        else:
            print(f"❌ Error: {message}")
            print("ℹ️  No hay credenciales guardadas. Por favor use la Opción 1 primero.")
            return False
    
    print("\n📊 Estado final del sistema:")
    final_status = get_status()
    print(f"📱 Cuentas activas: {final_status['accounts']['total']}")
    print(f"👤 Usuarios: {', '.join(final_status['accounts']['usernames'])}")
    
    # Demostración de envío de mensaje
    if final_status['accounts']['total'] > 0:
        print("\n💬 Demostración de envío de mensaje automático")
        username = final_status['accounts']['usernames'][0]
        recipient = input("Ingrese el usuario destinatario: ").strip()
        
        if recipient:
            message = f"🤖 Mensaje automático de prueba desde {username} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(f"🔄 Enviando mensaje automáticamente...")
            
            success, result = await auto_message(username, recipient, message)
            
            if success:
                print(f"✅ {result}")
                print(f"✅ Mensaje enviado: {message}")
            else:
                print(f"❌ Error enviando mensaje: {result}")
    
    print("\n🎉 Demostración completada")
    print("=" * 60)
    print("✅ Todo el proceso fue automático")
    print("✅ IP detectada automáticamente")
    print("✅ Dispositivo configurado automáticamente")
    print("✅ Login realizado automáticamente")
    print("✅ Sesión guardada automáticamente")
    print("✅ Credenciales encriptadas y guardadas")
    
    return True

async def demo_quick_setup():
    """Setup rápido para usuarios que ya tienen credenciales guardadas"""
    print("⚡ Setup Rápido Automático")
    print("=" * 40)
    
    print("🔄 Intentando login automático con credenciales guardadas...")
    success, message = await auto_login_saved()
    
    if success:
        print(f"✅ {message}")
        
        status = get_status()
        print(f"📱 Cuentas activas: {status['accounts']['total']}")
        print(f"👤 Usuario: {', '.join(status['accounts']['usernames'])}")
        
        return True
    else:
        print(f"❌ {message}")
        print("ℹ️  No hay credenciales guardadas. Ejecute la demostración completa primero.")
        return False

def show_system_info():
    """Muestra información del sistema"""
    print("ℹ️  Información del Sistema Automático")
    print("=" * 50)
    
    status = get_status()
    
    print("🌐 Configuración de Red:")
    print(f"  📍 IP Pública: {status['auto_config']['ip']}")
    print(f"  🖥️  Device ID: {status['auto_config']['device_id']}")
    print(f"  🌐 User-Agent: {status['auto_config']['user_agent'][:50]}...")
    
    print("\n🔐 Autenticación:")
    print(f"  💾 Credenciales guardadas: {status['auto_auth']['has_saved_credentials']}")
    print(f"  📊 Sesiones guardadas: {status['auto_auth']['has_saved_sessions']}")
    print(f"  👤 Usuarios: {', '.join(status['auto_auth']['saved_usernames']) if status['auto_auth']['saved_usernames'] else 'Ninguno'}")
    
    print("\n📱 Cuentas Instagram:")
    print(f"  📊 Total: {status['accounts']['total']}")
    print(f"  👤 Activas: {', '.join(status['accounts']['usernames']) if status['accounts']['usernames'] else 'Ninguna'}")
    
    print("\n🔧 Configuraciones guardadas:")
    print(f"  📁 Archivos: {len(status['saved_configs'])}")
    print(f"  👤 Usuarios: {', '.join(status['saved_configs']) if status['saved_configs'] else 'Ninguno'}")
    
    print(f"\n📊 Estado del sistema: {status['system_status']}")

async def main():
    """Función principal con menú interactivo"""
    print("🤖 Instagram API Automática - Menú Principal")
    print("=" * 50)
    
    while True:
        print("\n📋 Opciones disponibles:")
        print("1. 🚀 Demostración completa (setup automático)")
        print("2. ⚡ Setup rápido (con credenciales guardadas)")
        print("3. ℹ️  Ver información del sistema")
        print("4. 🧹 Limpiar todos los datos")
        print("5. ❌ Salir")
        
        choice = input("\nSeleccione una opción (1-5): ").strip()
        
        if choice == '1':
            await demo_auto_setup()
        elif choice == '2':
            await demo_quick_setup()
        elif choice == '3':
            show_system_info()
        elif choice == '4':
            confirm = input("⚠️  ¿Está seguro de limpiar todos los datos? (s/N): ").strip().lower()
            if confirm == 's':
                success = instagram_auto.reset_all()
                if success:
                    print("✅ Todos los datos han sido limpiados")
                else:
                    print("❌ Error limpiando datos")
        elif choice == '5':
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Por favor seleccione 1-5.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        logging.error(f"Error inesperado en demo: {e}")