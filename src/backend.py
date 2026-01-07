"""
SoundBoard Manager - Backend optimizado
Nota: Se usa pycaw/comtypes. En Python 3.14 comtypes puede fallar con
_compointer_base; se parchea de forma defensiva.
"""
import os
import json
import base64
import time
import io
import psutil
from PIL import Image
from pathlib import Path
import base64
import io


def _safe_import_comtypes():
    """Carga comtypes inyectando _compointer_base antes de ejecutar el módulo.

    En Python 3.14 comtypes 1.1.x falla porque referencia _compointer_base
    durante la inicialización. Al predefinirlo en el dict del módulo evitamos
    el NameError sin tocar site-packages.
    """
    import importlib.util
    import sys

    try:
        # Si hay un import previo fallido, limpiamos
        for name in list(sys.modules.keys()):
            if name.startswith('comtypes'):
                sys.modules.pop(name, None)

        import ctypes

        class _PointerDummy(ctypes.c_void_p):
            pass

        spec = importlib.util.find_spec('comtypes')
        if not spec or not spec.loader:
            print('[COMTYPES] Especificación no encontrada')
            return None

        mod = importlib.util.module_from_spec(spec)
        mod.__dict__['_compointer_base'] = _PointerDummy
        sys.modules['comtypes'] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f"[COMTYPES] Patch failed: {e}")
        return None


def _ensure_commethod():
    """Garantiza que comtypes exponga COMMETHOD (faltante en algunos builds)."""
    try:
        import comtypes
        if hasattr(comtypes, "COMMETHOD"):
            return
        try:
            from comtypes import _meta
            if hasattr(_meta, "COMMETHOD"):
                comtypes.COMMETHOD = _meta.COMMETHOD  # type: ignore[attr-defined]
                return
        except Exception:
            pass
        try:
            from comtypes import _cominterface
            if hasattr(_cominterface, "COMMETHOD"):
                comtypes.COMMETHOD = _cominterface.COMMETHOD  # type: ignore[attr-defined]
                return
        except Exception:
            pass
        try:
            from comtypes import _methods
            if hasattr(_methods, "COMMETHOD"):
                comtypes.COMMETHOD = _methods.COMMETHOD  # type: ignore[attr-defined]
                return
        except Exception:
            pass
        # Fallback: definir stub mínimo para permitir import de pycaw
        def _commethod_stub(*args, **kwargs):  # type: ignore[unused-argument]
            return (args, kwargs)
        comtypes.COMMETHOD = _commethod_stub  # type: ignore[assignment]
        print("[COMTYPES] COMMETHOD no disponible tras intentos de parcheo")
    except Exception as e:
        print(f"[COMTYPES] Error asegurando COMMETHOD: {e}")


def _ensure_iunknown():
    """Garantiza que comtypes exponga IUnknown (necesario para pycaw)."""
    try:
        import comtypes
        if hasattr(comtypes, "IUnknown"):
            return
        try:
            from comtypes import _cominterface
            if hasattr(_cominterface, "IUnknown"):
                comtypes.IUnknown = _cominterface.IUnknown  # type: ignore[attr-defined]
                return
        except Exception:
            pass
        try:
            from comtypes import _comobject
            if hasattr(_comobject, "IUnknown"):
                comtypes.IUnknown = _comobject.IUnknown  # type: ignore[attr-defined]
                return
        except Exception:
            pass
        # Fallback mínimo para evitar ImportError; puede limitar funcionalidad COM
        import ctypes
        class _IUnknownStub(ctypes.Structure):  # pragma: no cover - stub de emergencia
            _iid_ = None
            _methods_ = []
            _fields_ = []
        comtypes.IUnknown = _IUnknownStub  # type: ignore[assignment]
        print("[COMTYPES] IUnknown no disponible; se usó stub de emergencia")
    except Exception as e:
        print(f"[COMTYPES] Error asegurando IUnknown: {e}")


try:
    import comtypes  # noqa: F401
except Exception as e:
    print(f"[COMTYPES] Import error, applying patch: {e}")
    _safe_import_comtypes()
_ensure_commethod()
_ensure_iunknown()
def _ensure_stdmethod():
    """Garantiza que comtypes exponga STDMETHOD (alias habitual de COMMETHOD)."""
    try:
        import comtypes
        if hasattr(comtypes, "STDMETHOD"):
            return
        # Reutilizar COMMETHOD si existe
        if hasattr(comtypes, "COMMETHOD"):
            comtypes.STDMETHOD = comtypes.COMMETHOD  # type: ignore[assignment]
            return
        # Intentar cargar desde módulos internos
        for mod_name in ("_meta", "_methods", "_cominterface"):
            try:
                mod = __import__(f"comtypes.{mod_name}", fromlist=["*"])
                if hasattr(mod, "STDMETHOD"):
                    comtypes.STDMETHOD = getattr(mod, "STDMETHOD")  # type: ignore[assignment]
                    return
                if hasattr(mod, "COMMETHOD"):
                    comtypes.STDMETHOD = getattr(mod, "COMMETHOD")  # type: ignore[assignment]
                    return
            except Exception:
                pass
        # Fallback: alias a COMMETHOD de módulo base si se definió stub antes
        if hasattr(comtypes, "COMMETHOD"):
            comtypes.STDMETHOD = comtypes.COMMETHOD  # type: ignore[assignment]
            return
        print("[COMTYPES] STDMETHOD no disponible tras intentos de parcheo")
    except Exception as e:
        print(f"[COMTYPES] Error asegurando STDMETHOD: {e}")

_ensure_stdmethod()
def _ensure_bstr():
    """Garantiza que comtypes exponga BSTR (usado en automation)."""
    try:
        import comtypes
        if hasattr(comtypes, "BSTR"):
            return
        try:
            import comtypes.automation as _auto
            if hasattr(_auto, "BSTR"):
                comtypes.BSTR = _auto.BSTR  # type: ignore[assignment]
                return
        except Exception:
            pass
        import ctypes
        comtypes.BSTR = ctypes.c_wchar_p  # type: ignore[assignment]
        print("[COMTYPES] BSTR no encontrado; se asignó ctypes.c_wchar_p como fallback")
    except Exception as e:
        print(f"[COMTYPES] Error asegurando BSTR: {e}")

_ensure_bstr()
def _ensure_cocreateinstance():
    """Garantiza que comtypes exponga CoCreateInstance (usado por pycaw)."""
    try:
        import comtypes
        if hasattr(comtypes, "CoCreateInstance"):
            return
        try:
            # Reutilizar implementación de comtypes.client si está disponible
            from comtypes import client
            def _cocreate(clsid, clsctx=None, interface=None, outer=None):
                # Si interface es None, permitir objeto dinámico sin IID
                dynamic = interface is None
                return client.CreateObject(clsid, interface=interface, dynamic=dynamic)
            comtypes.CoCreateInstance = _cocreate  # type: ignore[assignment]
            return
        except Exception:
            pass
        # Fallback mínimo: usar ole32.CoCreateInstance vía ctypes
        try:
            import ctypes
            from ctypes import wintypes
            CLSCTX_INPROC_SERVER = 1
            CLSCTX_LOCAL_SERVER = 4
            _ole32 = ctypes.OleDLL("ole32")
            _ole32.CoCreateInstance.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
            _ole32.CoCreateInstance.restype = ctypes.c_long

            def _cocreate_raw(clsid, clsctx=CLSCTX_INPROC_SERVER | CLSCTX_LOCAL_SERVER, interface=None, outer=None):
                iid = getattr(interface, "_iid_", None) if interface else None
                if iid is None:
                    try:
                        from comtypes import IUnknown  # type: ignore
                        iid = getattr(IUnknown, "_iid_", None)
                    except Exception:
                        iid = None
                if iid is None:
                    # Sin IID, usar IID_IUnknown
                    from ctypes.wintypes import BYTE
                    class GUID(ctypes.Structure):
                        _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort), ("Data3", ctypes.c_ushort), ("Data4", BYTE * 8)]
                    IID_IUnknown = GUID(0x00000000, 0x0000, 0x0000, (BYTE * 8)(0xC0,0x00,0x00,0x00,0x00,0x00,0x00,0x46))
                    iid = IID_IUnknown
                if hasattr(iid, '__call__'):
                    iid = iid()
                punk = ctypes.c_void_p()
                hr = _ole32.CoCreateInstance(ctypes.byref(clsid), None, clsctx, ctypes.byref(iid), ctypes.byref(punk))
                if hr != 0:
                    raise OSError(hr, "CoCreateInstance failed")
                if interface:
                    return ctypes.cast(punk, ctypes.POINTER(interface))
                return punk

            comtypes.CoCreateInstance = _cocreate_raw  # type: ignore[assignment]
            return
        except Exception:
            pass
        print("[COMTYPES] CoCreateInstance no disponible tras intentos de parcheo")
    except Exception as e:
        print(f"[COMTYPES] Error asegurando CoCreateInstance: {e}")

_ensure_cocreateinstance()
from pycaw.pycaw import AudioUtilities

# Variables globales
last_master_volume = None
config_file = None
config_data = {}
config_mtime = None

def get_master_volume():
    """Obtiene volumen maestro actual"""
    try:
        from pycaw.pycaw import IAudioMeterInformation
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            AudioUtilities.IID_IAudioEndpointVolume, 0, None)
        volume = interface.GetMasterVolumeLevelScalar()
        return volume
    except:
        return None

def set_master_volume(level):
    """Establece volumen maestro"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            AudioUtilities.IID_IAudioEndpointVolume, 0, None)
        interface.SetMasterVolumeLevelScalar(level, None)
    except:
        pass


def toggle_master_mute():
    """Alterna el mute del volumen maestro."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            AudioUtilities.IID_IAudioEndpointVolume, 0, None)
        current = bool(interface.GetMute()) if hasattr(interface, 'GetMute') else False
        interface.SetMute(not current, None)
        return True
    except Exception as e:
        print(f"[AUDIO] Error toggle_master_mute: {e}")
        return False

def load_config():
    """Carga configuración desde settings.json"""
    global config_file, config_data, config_mtime
    try:
        appdata = os.getenv('APPDATA')
        config_dir = os.path.join(appdata, 'volume-mixer')
        config_file = os.path.join(config_dir, 'settings.json')
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            try:
                config_mtime = os.path.getmtime(config_file)
            except:
                config_mtime = None
                print(f"[CONFIG] Configuración cargada")
                return config_data
    except Exception as e:
        print(f"[CONFIG] Error cargando config: {e}")
    
    return {}

def refresh_config_if_changed():
    """Recarga configuración solo si el archivo cambió"""
    global config_mtime
    try:
        if config_file and os.path.exists(config_file):
            current_mtime = os.path.getmtime(config_file)
            if config_mtime is None or current_mtime != config_mtime:
                load_config()
    except Exception as e:
        print(f"[CONFIG] Error refrescando config: {e}")

def get_app_name_clean(pid):
    """Obtiene el nombre limpio de la aplicación"""
    try:
        process = psutil.Process(pid)
        exe_path = process.exe()
        base_name = os.path.basename(exe_path).lower()
        FRIENDLY = {
            'msedge.exe': 'Microsoft Edge',
            'chrome.exe': 'Google Chrome',
            'steam.exe': 'Steam',
            'telegram.exe': 'Telegram Desktop',
            'whatsapp.exe': 'WhatsApp',
            'spotify.exe': 'Spotify',
            'vlc.exe': 'VLC media player',
        }
        
        # Intentar obtener el nombre del producto desde el ejecutable
        import win32api
        try:
            info = win32api.GetFileVersionInfo(exe_path, '\\')
            lang, codepage = win32api.GetFileVersionInfo(exe_path, '\\VarFileInfo\\Translation')[0]
            string_file_info = f'\\StringFileInfo\\{lang:04X}{codepage:04X}\\'
            
            # Intentar obtener ProductName, si no FileDescription, si no el nombre del proceso
            for key in ['ProductName', 'FileDescription']:
                try:
                    name = win32api.GetFileVersionInfo(exe_path, string_file_info + key)
                    if name:
                        return name
                except:
                    pass
        except:
            pass
        
        # Fallback: nombre del proceso sin .exe
        if base_name in FRIENDLY:
            return FRIENDLY[base_name]
        return process.name().replace('.exe', '')
    except:
        return "Unknown"

def get_icon_from_shortcut(app_name):
    """Busca un acceso directo .lnk en Start Menu y extrae su icono.
    
    Intenta:
    - %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\<app_name>\\<app_name>.lnk
    - Búsqueda recursiva por nombre similar
    """
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        
        # Rutas posibles de Start Menu
        appdata = os.getenv('APPDATA', '')
        start_menu = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        
        if not os.path.exists(start_menu):
            return None
        
        # Buscar .lnk files recursivamente
        lnk_files = list(Path(start_menu).rglob('*.lnk'))
        
        # Prioridad: búsqueda exacta por nombre, luego búsqueda parcial
        candidates = []
        for lnk_path in lnk_files:
            lnk_name = lnk_path.stem.lower()
            app_lower = app_name.lower()
            if lnk_name == app_lower or app_lower in lnk_name or lnk_name in app_lower:
                candidates.append(lnk_path)
        
        if not candidates:
            return None
        
        # Usar el primer coincidente
        lnk_file = candidates[0]
        
        try:
            shortcut = shell.CreateShortcut(str(lnk_file))
            icon_path = shortcut.IconLocation  # Formato: "path,index" o ",index"
            target_path = shortcut.TargetPath
            
            if not icon_path and not target_path:
                return None
            
            # Parsear icon_path
            if icon_path:
                if ',' in icon_path:
                    icon_exe, icon_idx_str = icon_path.rsplit(',', 1)
                    try:
                        icon_idx = int(icon_idx_str)
                    except:
                        icon_idx = 0
                    # Si está vacío antes de la coma, usar target_path
                    if not icon_exe or icon_exe.strip() == '':
                        icon_exe = target_path
                else:
                    icon_exe = icon_path
                    icon_idx = 0
            else:
                # Sin IconLocation, usar TargetPath
                icon_exe = target_path
                icon_idx = 0
            
            # Limpiar comillas y espacios
            icon_exe = icon_exe.strip().strip('"')
            
            if icon_exe and os.path.exists(icon_exe):
                # Extraer icono desde la ruta indicada
                return extract_icon_from_file(icon_exe, icon_idx)
        except Exception as e:
            pass
        
        return None
    except Exception as e:
        return None


def extract_icon_from_file(file_path, index=0):
    """Extrae icono de un archivo (.exe, .dll, .ico) y lo convierte a PNG base64.
    
    Intenta:
    1. win32gui.ExtractIconEx
    2. Buscar PNG embebido en el archivo
    """
    try:
        import win32gui
        import win32ui
        import win32con
        
        large, small = win32gui.ExtractIconEx(file_path, index)
        hicon = None
        if large and len(large) > 0:
            hicon = large[0]
        elif small and len(small) > 0:
            hicon = small[0]
        
        if not hicon:
            return None
        
        iconinfo = win32gui.GetIconInfo(hicon)
        hbm_color = iconinfo['hbmColor']
        hbm_mask = iconinfo['hbmMask']
        
        hdc = win32gui.GetDC(0)
        srcdc = win32ui.CreateDCFromHandle(hdc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmapFromHandle(hbm_color)
        memdc.SelectObject(bmp)
        
        bmpinfo = bmp.GetInfo()
        width, height = bmpinfo['bmWidth'], bmpinfo['bmHeight']
        raw_bits = bmp.GetBitmapBits(True)
        
        img = Image.frombuffer('RGBA', (width, height), raw_bits, 'raw', 'BGRA', 0, 1)
        img = img.resize((24, 24), Image.LANCZOS)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        
        try:
            for ico in large:
                win32gui.DestroyIcon(ico)
            for ico in small:
                win32gui.DestroyIcon(ico)
        except Exception:
            pass
        
        return 'data:image/png;base64,' + b64
    except Exception:
        pass
    
    # Fallback: buscar PNG embebido en el archivo
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            png_header = b'\x89PNG\r\n\x1a\n'
            idx = data.find(png_header)
            
            if idx >= 0:
                # Buscar el final del PNG (IEND chunk)
                iend = data.find(b'IEND', idx) + 8
                if iend <= idx:
                    return None
                
                # Extraer PNG
                png_data = data[idx:iend]
                
                # Cargar con PIL
                img = Image.open(io.BytesIO(png_data))
                
                # Resize a 24x24
                img_resized = img.resize((24, 24), Image.LANCZOS)
                
                # Convertir a base64
                buf = io.BytesIO()
                img_resized.save(buf, format='PNG')
                b64 = base64.b64encode(buf.getvalue()).decode('ascii')
                
                return 'data:image/png;base64,' + b64
    except Exception:
        pass
    
    return None

def get_app_icon_base64(exe_path):
    """Extrae el icono del ejecutable y lo devuelve como PNG base64.

    Intenta:
    1. Extraer desde el ejecutable directamente
    2. Buscar en acceso directo .lnk del Start Menu
    
    Si falla, devuelve None.
    """
    if not exe_path:
        return None
    
    # Intenta extraer desde el ejecutable
    try:
        result = extract_icon_from_file(exe_path, 0)
        if result:
            return result
    except Exception:
        pass
    
    # Fallback: buscar en acceso directo
    try:
        # Extraer nombre amigable del ejecutable para búsqueda de .lnk
        app_name = os.path.basename(exe_path).replace('.exe', '')
        result = get_icon_from_shortcut(app_name)
        if result:
            return result
    except Exception:
        pass
    
    return None


# API simplificada para UI Tkinter
def list_sessions():
    """Devuelve lista de sesiones de audio activas.

    Cada elemento: name, pid, volume (0-100), isMuted (bool).
    """
    sessions_out = []
    try:
        sessions = AudioUtilities.GetAllSessions()
    except Exception as e:
        print(f"[AUDIO] Error obteniendo sesiones: {e}")
        return sessions_out

    for session in sessions:
        try:
            if not session.Process:
                continue
            pid = session.Process.pid
            volume_control = session.SimpleAudioVolume
            if not volume_control:
                continue
            volume = int(volume_control.GetMasterVolume() * 100)
            is_muted = bool(volume_control.GetMute()) if hasattr(volume_control, 'GetMute') else False
            name = get_app_name_clean(pid)
            sessions_out.append({
                "name": name,
                "pid": pid,
                "volume": volume,
                "isMuted": is_muted,
            })
        except Exception as e:
            print(f"[AUDIO] Error procesando sesión: {e}")
    return sessions_out


def set_app_volume(pid, volume):
    """Establece volumen (0-100) para una app por PID."""
    try:
        volume = max(0, min(100, int(volume)))
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.pid == pid:
                ctrl = session.SimpleAudioVolume
                if ctrl:
                    ctrl.SetMasterVolume(volume / 100.0, None)
                return True
    except Exception as e:
        print(f"[AUDIO] Error set_app_volume: {e}")
    return False


def toggle_mute(pid):
    """Alterna mute de una app por PID."""
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.pid == pid:
                ctrl = session.SimpleAudioVolume
                if ctrl and hasattr(ctrl, 'GetMute') and hasattr(ctrl, 'SetMute'):
                    current = bool(ctrl.GetMute())
                    ctrl.SetMute(not current, None)
                return True
    except Exception as e:
        print(f"[AUDIO] Error toggle_mute: {e}")
    return False


def get_master():
    """Volumen maestro (0-100)."""
    v = get_master_volume()
    return int(v * 100) if v is not None else None


def set_master(volume):
    """Ajusta volumen maestro (0-100)."""
    try:
        volume = max(0, min(100, int(volume)))
        set_master_volume(volume / 100.0)
        return True
    except Exception as e:
        print(f"[AUDIO] Error set_master: {e}")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--icons":
        print("Iconos extraídos:")
        for s in list_sessions():
            icon = get_app_icon_base64(psutil.Process(s['pid']).exe()) if s.get('pid') else None
            print(f"{s['name']} | icon_len={len(icon) if icon else 0}")
        sys.exit(0)
    else:
        print("Sesiones:")
        for s in list_sessions():
            print(s)

class AudioManager:
    """Gestiona sesiones de audio"""
    
    def __init__(self):
        self.sessions = []
        self.selected_index = 0
        self.navigation_mode = False
        self.icon_cache = {}
        self.name_cache = {}

# Métodos de AudioManager
def update_sessions(self):
    """Actualiza lista de sesiones con caché optimizado"""
    sessions_dict = {}
    sessions = AudioUtilities.GetAllSessions()
    
    for session in sessions:
        if not (session.Process and session.Process.name()):
            continue
            
        volume_control = session.SimpleAudioVolume
        if not volume_control:
            continue
            
        volume = int(volume_control.GetMasterVolume() * 100)
        is_muted = bool(volume_control.GetMute()) if hasattr(volume_control, 'GetMute') else False
        pid = session.Process.pid
        
        try:
            exe_path = session.Process.exe()
        except:
            exe_path = None
        
        # Obtener nombre con caché
        if exe_path and exe_path in self.name_cache:
            clean_name = self.name_cache[exe_path]
        else:
            clean_name = get_app_name_clean(pid)
            if exe_path:
                self.name_cache[exe_path] = clean_name
        
        # Obtener icono con caché
        if exe_path and exe_path in self.icon_cache:
            icon_data = self.icon_cache[exe_path]
        else:
            icon_data = get_app_icon_base64(exe_path)
            if exe_path:
                self.icon_cache[exe_path] = icon_data
        
        if not icon_data:
            icon_data = './assets/noicon.png'
        
        # Agrupar por nombre
        if clean_name not in sessions_dict:
            sessions_dict[clean_name] = {
                'name': clean_name,
                'icon': icon_data,
                'volume': volume,
                'pid': pid,
                'isMuted': is_muted,
                '_controls': [volume_control],
                '_mutes': [is_muted]
            }
        else:
            existing = sessions_dict[clean_name]
            existing['_controls'].append(volume_control)
            existing['volume'] = int(sum(vc.GetMasterVolume() * 100 for vc in existing['_controls']) / len(existing['_controls']))
            existing['_mutes'].append(is_muted)
            existing['isMuted'] = any(existing['_mutes'])
    
    # Convertir a lista
    self.sessions = []
    for session_data in sessions_dict.values():
        controls = session_data.pop('_controls')
        session_data.pop('_mutes', None)
        session_data['_controls'] = controls
        self.sessions.append(session_data)
    
    if self.selected_index >= len(self.sessions):
        self.selected_index = max(0, len(self.sessions) - 1)
    
    return self.get_state()

def get_state(self):
    """Obtiene estado actual"""
    sessions_data = []
    for i, session in enumerate(self.sessions):
        sessions_data.append({
            'name': session['name'],
            'icon': session['icon'],
            'volume': session['volume'],
            'isSelected': i == self.selected_index,
            'isMuted': session.get('isMuted', False)
        })
    
    return {
        'sessions': sessions_data,
        'selectedIndex': self.selected_index,
        'navigationMode': self.navigation_mode
    }

def set_volume(self, index, volume):
    """Establece volumen de una sesión"""
    if not (0 <= index < len(self.sessions)):
        return False
    
    session = self.sessions[index]
    for control in session.get('_controls', []):
        try:
            control.SetMasterVolume(volume / 100.0, None)
        except:
            pass
    session['volume'] = volume
    return True

# Reasignar métodos a la clase
AudioManager.update_sessions = update_sessions
AudioManager.get_state = get_state
AudioManager.set_volume = set_volume

def change_volume(self, delta):
    """Cambia volumen de sesión seleccionada y desmutea automáticamente"""
    if not self.sessions:
        return None
    
    session = self.sessions[self.selected_index]
    new_vol = max(0, min(100, session['volume'] + delta))
    
    # Desmutear al ajustar volumen
    if session.get('isMuted', False):
        for control in session.get('_controls', []):
            try:
                control.SetMute(False, None)
            except:
                pass
        session['isMuted'] = False
    
    self.set_volume(self.selected_index, new_vol)
    return self.get_state()

def next_session(self):
    """Siguiente sesión"""
    if self.sessions:
        self.selected_index = (self.selected_index + 1) % len(self.sessions)
    return self.get_state()

def prev_session(self):
    """Sesión anterior"""
    if self.sessions:
        self.selected_index = (self.selected_index - 1) % len(self.sessions)
    return self.get_state()

AudioManager.change_volume = change_volume
AudioManager.next_session = next_session
AudioManager.prev_session = prev_session


class VolumeApp:
    """Aplicación integrada"""
    
    def __init__(self):
        self.audio_manager = AudioManager()
        self.clients = set()
        self.loop = None
        self.electron_process = None
        self.last_session_count = 0
        self.update_interval = 1  # Actualizar cada 1 segundo
    
    async def register(self, websocket):
        """Registra cliente"""
        self.clients.add(websocket)
        await websocket.send(json.dumps({
            'type': 'state',
            'data': self.audio_manager.update_sessions()
        }))
        print(f"[OK] Cliente conectado. Total: {len(self.clients)}")
    
    async def unregister(self, websocket):
        """Desregistra cliente"""
        self.clients.discard(websocket)
        print(f"[DISCONNECTED] Cliente desconectado. Total: {len(self.clients)}")
    
    async def broadcast(self, message):
        """Envía mensaje a todos"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
    
    async def update_sessions_periodically(self):
        """Actualiza sesiones periódicamente solo si hay cambios"""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                state = self.audio_manager.update_sessions()
                current_count = len(state.get('sessions', []))
                
                if current_count != self.last_session_count:
                    self.last_session_count = current_count
                    await self.broadcast(json.dumps({
                        'type': 'state',
                        'data': state
                    }))
            except Exception as e:
                print(f"[UPDATE] Error: {e}")
    
    async def handler(self, websocket):
        """Handler WebSocket"""
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    if msg_type == 'get_state':
                        state = self.audio_manager.update_sessions()
                        await websocket.send(json.dumps({
                            'type': 'state',
                            'data': state
                        }))
                except Exception as e:
                    print(f"Error: {e}")
        finally:
            await self.unregister(websocket)
    
    def handle_keyboard(self, event):
        """Maneja eventos de teclado de forma optimizada"""
        global last_master_volume

        if event.event_type != 'down':
            return True
        
        # Refrescar configuración si cambió
        refresh_config_if_changed()
        
        volume_up = event.name == 'volume up'
        volume_down = event.name == 'volume down'
        volume_mute = event.name == 'volume mute'
        
        if not (volume_up or volume_down or volume_mute):
            return True
        
        # Guardar volumen maestro
        last_master_volume = get_master_volume()
        
        state = None
        
        if volume_mute:
            self.audio_manager.navigation_mode = not self.audio_manager.navigation_mode
            state = self.audio_manager.get_state()
        elif volume_up or volume_down:
            if self.audio_manager.navigation_mode:
                state = self.audio_manager.next_session() if volume_up else self.audio_manager.prev_session()
            else:
                volume_delta = config_data.get('volumeDelta', 5)
                delta = volume_delta if volume_up else -volume_delta
                state = self.audio_manager.change_volume(delta)
        
        # Enviar actualizaciones
        if state:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(json.dumps({'type': 'show'})),
                    self.loop
                )
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(json.dumps({'type': 'state', 'data': state})),
                    self.loop
                )
            except Exception as e:
                print(f"[ERROR] {e}")
        
        # Restaurar volumen maestro
        if last_master_volume is not None:
            time.sleep(0.05)
            current_volume = get_master_volume()
            if current_volume != last_master_volume:
                set_master_volume(last_master_volume)
        
        return False
    
    
    async def start_server(self):
        """Inicia servidor WebSocket"""
        # Iniciar tarea de actualización periódica
        update_task = asyncio.create_task(self.update_sessions_periodically())
        
        async with websockets.serve(self.handler, "localhost", 8765):
            print("[OK] WebSocket server en ws://localhost:8765")
            await asyncio.Future()  # run forever
    
    def run(self):
        """Inicia la aplicación de forma optimizada"""
        print("\n" + "="*60)
        print("  SOUNDBOARD MANAGER")
        print("="*60 + "\n")
        
        load_config()
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        keyboard.hook(self.handle_keyboard, suppress=True)
        print("[OK] Sistema iniciado\n")
        
        refresh_config_if_changed()

        try:
            self.loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Cerrando...")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            keyboard.unhook_all()
            try:
                self.loop.close()
            except:
                pass


if __name__ == "__main__":
    app = VolumeApp()
    app.run()
