#!/usr/bin/env python3
"""
SoundBoard Manager - Punto de entrada unificado
Versión simplificada con UI nativa Tkinter (sin dependencias pesadas)
Ejecuta en background: la UI está oculta por defecto y se muestra solo al usar la rueda multimedia.
"""

from . import media_wheel
from . import i18n
import threading
import json
from pathlib import Path

# Opcional: bandeja del sistema para salir
def on_exit(icon, item):
    global media_hw, app
    try:
        if media_hw:
            media_hw.stop()
    except:
        pass
    try:
        if app and hasattr(app, 'app'):
            app.app.quit()
    except:
        pass
    icon.visible = False
    icon.stop()

def on_show(icon, item):
    global app
    try:
        if app and hasattr(app, 'win') and hasattr(app.win, 'requestShow'):
            app.win.requestShow.emit()
    except Exception:
        pass

def on_hide(icon, item):
    global app
    try:
        if app and hasattr(app, 'win') and hasattr(app.win, 'requestHide'):
            app.win.requestHide.emit()
    except Exception:
        pass

def on_settings(icon, item):
    global app
    try:
        if app and hasattr(app, 'win') and hasattr(app.win, 'requestSettings'):
            app.win.requestSettings.emit()
            # Actualizar menú después de cambiar configuración
            import time
            time.sleep(0.5)  # Esperar a que se guarde la config
            update_tray_menu()
    except Exception:
        pass

def _start_tray():
    global tray_icon
    try:
        import pystray
        from PIL import Image, ImageDraw

        def create_image():
            # Usar icono real del proyecto
            try:
                icon_path = Path(__file__).parent / 'assets' / 'icon.png'
                if icon_path.exists():
                    return Image.open(icon_path)
            except Exception:
                pass
            # Fallback simple
            img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rectangle([2, 2, 14, 14], fill=(255, 255, 255, 255))
            return img

        # Obtener idioma de configuración para el menú
        try:
            from . import ui_qt
            config = ui_qt.load_config()
            lang = config.get('language', 'es')
            i18n_inst = i18n.get_i18n(lang)
        except Exception:
            i18n_inst = i18n.get_i18n('es')

        tray_icon = pystray.Icon(
            'SoundBoard',
            create_image(),
            'SoundBoard',
            menu=pystray.Menu(
                pystray.MenuItem(i18n_inst.t('tray_show'), on_show),
                pystray.MenuItem(i18n_inst.t('tray_hide'), on_hide),
                pystray.MenuItem(i18n_inst.t('tray_settings'), on_settings),
                pystray.MenuItem(i18n_inst.t('tray_exit'), on_exit)
            )
        )
        tray_icon.run()
    except Exception as e:
        print(f"[TRAY] No se pudo iniciar bandeja: {e}")

media_hw = None
app = None
tray_icon = None

def update_tray_menu():
    """Actualiza el menú de la bandeja con el idioma actual"""
    global tray_icon
    if tray_icon:
        try:
            from . import ui_qt
            config = ui_qt.load_config()
            lang = config.get('language', 'es')
            i18n_inst = i18n.get_i18n(lang)
            i18n_inst.set_language(lang)
            
            # Recrear el menú con las traducciones actualizadas
            def on_show_wrapper(icon, item):
                on_show(icon, item)
            def on_hide_wrapper(icon, item):
                on_hide(icon, item)
            def on_settings_wrapper(icon, item):
                on_settings(icon, item)
            def on_exit_wrapper(icon, item):
                on_exit(icon, item)
            
            import pystray
            tray_icon.menu = pystray.Menu(
                pystray.MenuItem(i18n_inst.t('tray_show'), on_show_wrapper),
                pystray.MenuItem(i18n_inst.t('tray_hide'), on_hide_wrapper),
                pystray.MenuItem(i18n_inst.t('tray_settings'), on_settings_wrapper),
                pystray.MenuItem(i18n_inst.t('tray_exit'), on_exit_wrapper)
            )
            tray_icon.update_menu()
        except Exception as e:
            print(f"[TRAY] Error actualizando menú: {e}")

def run_ui():
    """Inicia la UI Qt (corre en hilo principal)"""
    global app
    try:
        from . import ui_qt
        app = ui_qt.SoundBoardUI(None, media_hw)
        app.run()
    except Exception as e:
        print(f"[UI] Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Punto de entrada principal - lanza en background"""
    global media_hw
    print("[SOUNDBOARD] Iniciando SoundBoard Manager...")
    print("[SOUNDBOARD] Python versión optimizada (sin Electron)")
    print("[SOUNDBOARD] Interfaz en background - usa la rueda multimedia para mostrar")

    try:
        media_hw = media_wheel.start_media_wheel(step=4, hold_ms=2000)
    except Exception as e:
        print(f"[MEDIA-WHEEL] No se pudo iniciar la rueda multimedia: {e}")

    # Iniciar bandeja en hilo aparte (si disponible)
    tray_thread = threading.Thread(target=_start_tray, daemon=True)
    tray_thread.start()

    # Iniciar UI directamente (bloquea el hilo principal)
    run_ui()

    if media_hw:
        media_hw.stop()
    print("[SOUNDBOARD] Cerrando...")

if __name__ == '__main__':
    main()

