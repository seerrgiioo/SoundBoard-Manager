#!/usr/bin/env python3
"""
Script de build mejorado para SoundBoard Manager
Crea versión portable y versión instalable
"""
import subprocess
import sys
import shutil
from pathlib import Path
import os

def install_pyinstaller():
    """Instala PyInstaller si no está disponible"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller encontrado: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller no encontrado")
        print("  Instalando PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✓ PyInstaller instalado")
            return True
        except Exception as e:
            print(f"✗ Error instalando PyInstaller: {e}")
            return False

def build_portable():
    """Construye la versión portable (un solo .exe)"""
    print("\n" + "=" * 60)
    print("CONSTRUYENDO VERSIÓN PORTABLE")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    icon_file = project_dir / "src" / "assets" / "icon.ico"
    
    args = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "SoundBoardManager-Portable",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath", "dist/portable",
        "--workpath", "build/portable",
        "--specpath", "build",
    ]
    
    if icon_file.exists():
        args.extend(["--icon", str(icon_file)])
    
    args.extend([
        "--add-data", f"{project_dir / 'src' / 'assets'}{os.pathsep}assets",
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
        str(project_dir / "src" / "__main__.py"),
    ])
    
    try:
        subprocess.run(args, check=True)
        exe_file = project_dir / "dist" / "portable" / "SoundBoardManager-Portable.exe"
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"\n✓ Versión portable creada: {exe_file}")
            print(f"  Tamaño: {size_mb:.2f} MB")
            return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error creando versión portable: {e}")
        return False

def build_installer():
    """Construye la versión instalable (carpeta con archivos)"""
    print("\n" + "=" * 60)
    print("CONSTRUYENDO VERSIÓN INSTALABLE")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    icon_file = project_dir / "src" / "assets" / "icon.ico"
    
    args = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", "SoundBoardManager",
        "--onedir",  # Carpeta en lugar de un solo archivo
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath", "dist/installer",
        "--workpath", "build/installer",
        "--specpath", "build",
    ]
    
    if icon_file.exists():
        args.extend(["--icon", str(icon_file)])
    
    args.extend([
        "--add-data", f"{project_dir / 'src' / 'assets'}{os.pathsep}assets",
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
        str(project_dir / "src" / "__main__.py"),
    ])
    
    try:
        subprocess.run(args, check=True)
        exe_file = project_dir / "dist" / "installer" / "SoundBoardManager" / "SoundBoardManager.exe"
        if exe_file.exists():
            print(f"\n✓ Versión instalable creada: {exe_file.parent}")
            return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error creando versión instalable: {e}")
        return False

def create_nsis_script():
    """Crea el script NSIS para el instalador"""
    print("\n" + "=" * 60)
    print("CREANDO SCRIPT DE INSTALADOR")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    nsis_script = project_dir / "installer.nsi"
    
    script_content = '''
; SoundBoard Manager - Script de instalación NSIS
; Requiere NSIS 3.0 o superior

!define APPNAME "SoundBoard Manager"
!define COMPANYNAME "SoundBoard"
!define DESCRIPTION "Lightweight volume mixer for Windows"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define INSTALLSIZE 30000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\\${APPNAME}"
Name "${APPNAME}"
Icon "src\\assets\\icon.ico"
outFile "dist\\SoundBoardManager-Setup.exe"

!include LogicLib.nsh
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "src\\assets\\icon.ico"
!define MUI_UNICON "src\\assets\\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "English"

Section "install"
    SetOutPath $INSTDIR
    
    ; Copiar archivos
    File /r "dist\\installer\\SoundBoardManager\\*.*"
    
    ; Crear acceso directo en el menú inicio
    CreateDirectory "$SMPROGRAMS\\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\SoundBoardManager.exe"
    CreateShortCut "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    
    ; Crear acceso directo en el escritorio (opcional)
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\SoundBoardManager.exe"
    
    ; Registro para agregar/quitar programas
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\SoundBoardManager.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    ; Iniciar con Windows (HKCU Run)
    WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Run" "${APPNAME}" "$INSTDIR\\SoundBoardManager.exe"
    
    ; Crear desinstalador
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "uninstall"
    ; Eliminar archivos
    RMDir /r "$INSTDIR"
    
    ; Eliminar accesos directos
    Delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\${APPNAME}"
    Delete "$DESKTOP\\${APPNAME}.lnk"
    
    ; Eliminar del inicio automático
    DeleteRegValue HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Run" "${APPNAME}"
    
    ; Eliminar entradas del registro
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
SectionEnd
'''
    
    try:
        with open(nsis_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"✓ Script NSIS creado: {nsis_script}")
        print("  (Se compilará automáticamente en el siguiente paso si NSIS está instalado)")
        return True
    except Exception as e:
        print(f"✗ Error creando script NSIS: {e}")
        return False

def build_nsis_installer():
    """Ejecuta makensis para generar el instalador .exe"""
    print("\n" + "=" * 60)
    print("COMPILANDO INSTALADOR NSIS")
    print("=" * 60)

    project_dir = Path(__file__).parent
    nsis_script = project_dir / "installer.nsi"
    makensis = shutil.which("makensis")

    if not nsis_script.exists():
        print("✗ Script NSIS no encontrado. Ejecuta create_nsis_script primero.")
        return False

    if not makensis:
        print("✗ NSIS (makensis) no está en PATH. Instálalo desde https://nsis.sourceforge.io/Download y reinicia la terminal.")
        return False

    try:
        subprocess.run([makensis, str(nsis_script)], check=True)
        setup_path = project_dir / "dist" / "SoundBoardManager-Setup.exe"
        if setup_path.exists():
            print(f"✓ Instalador generado: {setup_path}")
            return True
        print("✗ makensis se ejecutó pero no se encontró el instalador.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"✗ Error ejecutando makensis: {e}")
        return False

def install_built_setup():
    """Ejecuta el instalador generado en modo silencioso para instalarlo localmente."""
    print("\n" + "=" * 60)
    print("INSTALANDO APLICACIÓN (SILENCIOSO)")
    print("=" * 60)

    project_dir = Path(__file__).parent
    setup_path = project_dir / "dist" / "SoundBoardManager-Setup.exe"

    if not setup_path.exists():
        print("✗ No se encontró dist/SoundBoardManager-Setup.exe. Ejecuta el paso de NSIS.")
        return False

    try:
        subprocess.run([str(setup_path), "/S"], check=True)
        print("✓ Instalación completada. La app se agregará al inicio de Windows.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error instalando el setup: {e}")
        return False

def main():
    print("=" * 60)
    print("SOUNDBOARD MANAGER - BUILD SCRIPT")
    print("=" * 60)
    
    # Verificar PyInstaller
    if not install_pyinstaller():
        sys.exit(1)
    
    # Limpiar builds anteriores
    project_dir = Path(__file__).parent
    for path in ["dist", "build"]:
        full_path = project_dir / path
        if full_path.exists():
            print(f"Limpiando {path}/...")
            shutil.rmtree(full_path, ignore_errors=True)
    
    success = True
    
    # Build portable
    if not build_portable():
        success = False
    
    # Build installer
    if not build_installer():
        success = False
    
    # Crear script NSIS
    if not create_nsis_script():
        success = False
    
    # Compilar instalador NSIS
    if success and not build_nsis_installer():
        success = False
    
    # Instalar automáticamente (silent)
    if success and not install_built_setup():
        success = False
    
    # Resumen
    print("\n" + "=" * 60)
    if success:
        print("✓ BUILD COMPLETADO")
        print("=" * 60)
        print("\nArchivos generados:")
        print("  • Portable: dist/portable/SoundBoardManager-Portable.exe")
        print("  • Instalable (carpeta): dist/installer/SoundBoardManager/")
        print("  • Script instalador: installer.nsi")
        print("  • Instalador NSIS: dist/SoundBoardManager-Setup.exe")
        print("\nInstalación completada en el sistema local (modo silencioso).")
    else:
        print("✗ BUILD COMPLETADO CON ERRORES")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
