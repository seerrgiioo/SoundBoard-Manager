#!/usr/bin/env python3
"""
Script de build para SoundBoard Manager
Crea un ejecutable independiente con PyInstaller
"""
import subprocess
import sys
import shutil
from pathlib import Path

def build():
    print("=" * 60)
    print("SoundBoard Manager - Build Script")
    print("=" * 60)
    
    # Verificar PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller encontrado: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller no encontrado")
        print("  Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✓ PyInstaller instalado")
    
    # Rutas
    project_dir = Path(__file__).parent
    src_dir = project_dir / "src"
    icon_file = src_dir / "assets" / "icon.ico"
    
    # Verificar icono
    if not icon_file.exists():
        print(f"⚠ Icono no encontrado: {icon_file}")
        icon_arg = []
    else:
        print(f"✓ Icono encontrado: {icon_file}")
        icon_arg = ["--icon", str(icon_file)]
    
    # Argumentos de PyInstaller
    args = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "SoundBoardManager",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        # Datos adicionales
        "--add-data", f"{src_dir / 'assets'}:assets",
        # Ocultar imports
        "--hidden-import", "pycaw",
        "--hidden-import", "keyboard",
        "--hidden-import", "comtypes",
        "--hidden-import", "psutil",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32con",
        "--hidden-import", "win32api",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--hidden-import", "PySide6",
        # Punto de entrada
        "-m", "src",
    ]
    
    # Añadir icono si existe
    if icon_arg:
        args.extend(icon_arg)
    
    print("\n" + "=" * 60)
    print("Iniciando build...")
    print("=" * 60)
    print(f"Comando: {' '.join(args)}\n")
    
    # Ejecutar PyInstaller
    try:
        result = subprocess.run(args, check=True)
        print("\n" + "=" * 60)
        print("✓ Build completado exitosamente")
        print("=" * 60)
        
        # Información de salida
        dist_dir = project_dir / "dist"
        exe_file = dist_dir / "SoundBoardManager.exe"
        
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"\nArchivo: {exe_file}")
            print(f"Tamaño: {size_mb:.2f} MB")
            print(f"\n✓ El ejecutable está listo en: {dist_dir}")
        else:
            print(f"\n⚠ Ejecutable no encontrado en {dist_dir}")
        
        print("\nNOTA: El ejecutable necesita los archivos de idioma en GitHub")
        print("      Ver CONFIGURACION_I18N.md para más detalles")
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("✗ Error durante el build")
        print("=" * 60)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
