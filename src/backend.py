"""
SoundBoard Manager - Backend optimizado
"""
from pycaw.pycaw import AudioUtilities
import keyboard
import asyncio
import websockets
import json
import os
import time
import psutil
import base64
from PIL import Image
import io
import numpy as np

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
        return process.name().replace('.exe', '')
    except:
        return "Unknown"

def get_app_icon_base64(exe_path):
    """Obtiene el icono de la aplicación en base64 con transparencia"""
    if not exe_path:
        return None
    
    try:
        import win32gui
        import win32ui
        import win32con
        
        large, small = win32gui.ExtractIconEx(exe_path, 0, 1)
        if not large or len(large) == 0:
            return None
        hicon = large[0]
        
        icon_size = 32
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hdc_mem = hdc.CreateCompatibleDC()
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, icon_size, icon_size)
        hdc_mem.SelectObject(hbmp)
        win32gui.DrawIconEx(hdc_mem.GetSafeHdc(), 0, 0, hicon, icon_size, icon_size, 0, 0, win32con.DI_NORMAL)
        
        bmpstr = hbmp.GetBitmapBits(True)
        img_rgb = Image.frombuffer('RGB', (icon_size, icon_size), bmpstr, 'raw', 'BGRX', 0, 1)
        arr = np.array(img_rgb)
        alpha = np.full((icon_size, icon_size), 255, dtype=np.uint8)
        rgba = np.dstack((arr, alpha))

        # Transparencia por flood-fill desde las esquinas
        def flood_clear(bg_color, threshold=12):
            h, w = icon_size, icon_size
            visited = np.zeros((h, w), dtype=bool)
            stack = [(0,0), (0,w-1), (h-1,0), (h-1,w-1)]
            while stack:
                y, x = stack.pop()
                if y<0 or y>=h or x<0 or x>=w or visited[y, x]:
                    continue
                visited[y, x] = True
                px = rgba[y, x, :3]
                if np.max(np.abs(px.astype(int) - bg_color.astype(int))) <= threshold:
                    rgba[y, x, 3] = 0
                    stack.extend([(y-1,x), (y+1,x), (y,x-1), (y,x+1)])

        corners = np.array([rgba[0,0,:3], rgba[0,-1,:3], rgba[-1,0,:3], rgba[-1,-1,:3]])
        bg_color = corners.mean(axis=0).astype(np.uint8)
        flood_clear(bg_color)

        img = Image.fromarray(rgba, 'RGBA')
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        win32gui.DestroyIcon(hicon)
        if small and len(small) > 0:
            win32gui.DestroyIcon(small[0])
        
        return f"data:image/png;base64,{img_base64}"
    except:
        return None

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
