#!/usr/bin/env python3
"""
🤖 Instagram Ultra-Automático - Demo Simplificada

Sistema 100% automático SIN cookies manuales, SIN configuración.
Solo usuario y contraseña - TODO lo demás es automático.

Características eliminadas:
- ❌ Sin cookies manuales de Instagram
- ❌ Sin sessionid manual
- ❌ Sin csrftoken manual
- ❌ Sin ds_user_id manual
- ❌ Sin DevTools ni cookies del navegador

Características automáticas:
- ✅ Solo usuario y contraseña
- ✅ IP detectada automáticamente
- ✅ Device ID generado automáticamente
- ✅ User-Agent configurado automáticamente
- ✅ Login automático con reintento
- ✅ Sesiones guardadas automáticamente
- ✅ Credenciales encriptadas automáticamente
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(str(Path(__file__).parent))

from app.instagram_ultra import (
    instagram_ultra,
    ultra_setup,
    ultra_login,
    ultra_message,
    ultra_status
)

async def demo_ultra_simple():
    """Demo ultra-simple: solo usuario y contraseña"""
    print("🚀 Instagram Ultra-Automático")
    print("=" * 50)
    print("✅ SIN cookies manuales")
    print("✅ SIN configuración")
    print("✅ SIN sessionid manual")
    print("✅ SIN csrftoken manual")
    print("✅ TODO automático con tu IP real")
    print()
    
    # Mostrar estado actual
    print("📊 Estado del sistema:")
    status = ultra_status()
    print(f"🌐 IP detectada: {status['network']['ip']}")
    print(f"📱 Device ID: {status['network']['device_id']}")
    print(f"💾 Credenciales guardadas: {status['credentials']['has_saved']}")
    print(f"📊 Cuentas activas: {status['accounts']['total']}")
    print()
    
    # Opciones simples
    print("📋 Opciones:")
    print("1. 🔐 Setup con usuario y contraseña (TODO automático)")
    print("2. ⚡ Login automático (con credenciales guardadas)")
    print("3. ℹ️  Ver estado")
    print("4. 🧹 Limpiar todo")
    print("5. ❌ Salir")
    print()
    
    choice = input("Seleccione (1-5): ").strip()
    
    if choice == '1':
        await ultra_simple_setup()
    elif choice == '2':
        await ultra_simple_login()
    elif choice == '3':
        show_ultra_status()
    elif choice == '4':
        await ultra_clean()
    elif choice == '5':
        print("👋 ¡Hasta luego!")
        return
    else:
        print("❌ Opción inválida")

async def ultra_simple_setup():
    """Setup ultra-simple: solo pide usuario y contraseña"""
    print("\n🔐 Setup Ultra-Simple")
    print("=" * 30)
    print("ℹ️  Ingrese solo usuario y contraseña")
    print("ℹ️  TODO lo demás es automático")
    print()
    
    username = input("👤 Usuario de Instagram: ").strip()
    if not username:
        print("❌ Usuario requerido")
        return
    
    password = input("🔑 Contraseña: ").strip()
    if not password:
        print("❌ Contraseña requerida")
        return
    
    print(f"\n🔄 Configurando {username} automáticamente...")
    print("🤖 Detectando IP automáticamente...")
    print("📱 Generando Device ID automáticamente...")
    print("🌐 Configurando User-Agent automáticamente...")
    print("🔐 Iniciando login automático...")
    
    # Setup ultra-automático
    success, message = await ultra_setup(username, password)
    
    if success:
        print(f"\n✅ {message}")
        print("✅ IP detectada y configurada automáticamente")
        print("✅ Device ID generado automáticamente")
        print("✅ User-Agent configurado automáticamente")
        print("✅ Login exitoso automáticamente")
        print("✅ Credenciales guardadas automáticamente")
        print("✅ Sesión guardada automáticamente")
        
        # Demo de envío de mensaje
        await demo_auto_message(username)
        
    else:
        print(f"\n❌ Error: {message}")
        print("ℹ️  El sistema reintentará automáticamente en el próximo intento")

async def ultra_simple_login():
    """Login automático con credenciales guardadas"""
    print("\n⚡ Login Automático")
    print("=" * 25)
    print("🔄 Usando credenciales guardadas...")
    
    success, message = await ultra_login()
    
    if success:
        print(f"✅ {message}")
        
        status = ultra_status()
        if status['credentials']['username']:
            await demo_auto_message(status['credentials']['username'])
    else:
        print(f"❌ {message}")
        print("ℹ️  No hay credenciales guardadas. Use la opción 1 primero.")

async def demo_auto_message(username: str):
    """Demo de envío automático de mensaje"""
    print("\n💬 Demo de Envío de Mensaje")
    print("=" * 30)
    
    recipient = input("👤 Usuario destinatario (deje vacío para saltar): ").strip()
    
    if recipient:
        message = f"🤖 Mensaje automático de prueba - {datetime.now().strftime('%H:%M:%S')}"
        print(f"🔄 Enviando mensaje automáticamente a {recipient}...")
        
        success, result = await ultra_message(username, recipient, message)
        
        if success:
            print(f"✅ {result}")
            print(f"✅ Mensaje enviado: {message}")
        else:
            print(f"❌ Error: {result}")
    else:
        print("ℹ️  Demo de mensaje omitida")

def show_ultra_status():
    """Muestra estado ultra-automático"""
    print("\nℹ️  Estado Ultra-Automático")
    print("=" * 35)
    
    status = ultra_status()
    
    print("🌐 Red:")
    print(f"  📍 IP detectada: {status['network']['ip']}")
    print(f"  📱 Device ID: {status['network']['device_id'][:8]}...")
    print(f"  🌐 User-Agent: {status['network']['user_agent'][:40]}...")
    
    print("\n🔐 Autenticación:")
    print(f"  💾 Credenciales guardadas: {status['credentials']['has_saved']}")
    if status['credentials']['username']:
        print(f"  👤 Usuario: {status['credentials']['username']}")
    
    print("\n📱 Cuentas:")
    print(f"  📊 Total: {status['accounts']['total']}")
    if status['accounts']['usernames']:
        print(f"  👤 Activas: {', '.join(status['accounts']['usernames'])}")
    
    print(f"\n🔧 Sistema: {status['system']['type']} - {status['system']['status']}")

async def ultra_clean():
    """Limpieza ultra-automática"""
    print("\n🧹 Limpiar Todo")
    print("=" * 20)
    
    confirm = input("⚠️  ¿Limpiar credenciales y configuraciones? (s/N): ").strip().lower()
    
    if confirm == 's':
        print("🔄 Limpiando sistema ultra-automático...")
        
        success = instagram_ultra.reset_ultra_system()
        
        if success:
            print("✅ Sistema limpiado completamente")
            print("✅ Credenciales eliminadas")
            print("✅ Configuraciones reseteadas")
            print("�️  Logs limpiados")
        else:
            print("❌ Error limpiando sistema")
    else:
        print("ℹ️  Limpieza cancelada")

async def main():
    """Función principal"""
    try:
        await demo_ultra_simple()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())