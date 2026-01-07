#!/usr/bin/env python3
"""
SoundBoard Manager - Punto de entrada unificado
Versión simplificada con UI nativa Tkinter (sin dependencias pesadas)
Ejecuta en background: la UI está oculta por defecto y se muestra solo al usar la rueda multimedia.
"""

from . import media_wheel
import threading
import json
from pathlib import Path

# Opcional: bandeja del sistema para salir
def _start_tray():
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
                if app and hasattr(app, 'win') and hasattr(app.win, 'show_settings'):
                    app.win.show_settings()
            except Exception:
                pass

        icon = pystray.Icon(
            'SoundBoard',
            create_image(),
            'SoundBoard',
            menu=pystray.Menu(
                pystray.MenuItem('Mostrar', on_show),
                pystray.MenuItem('Ocultar', on_hide),
                pystray.MenuItem('Configuración', on_settings),
                pystray.MenuItem('Salir', on_exit)
            )
        )
        icon.run()
    except Exception as e:
        print(f"[TRAY] No se pudo iniciar bandeja: {e}")

media_hw = None
app = None

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

