#!/usr/bin/env python3
"""
Intercepción de teclas multimedia (rueda del teclado) para tomar control total.
- Volumen arriba/abajo: ajusta volumen de la sesión seleccionada (o master si no hay apps), o navega si está en modo selección.
- Pulsar (mute): clic corto alterna modo volumen/selección; mantener 2s silencia la sesión actual (o master).
- Se suprime el manejo nativo del sistema (no cambia el volumen maestro por defecto).
"""
import keyboard
import threading
import time
from . import backend


class MediaWheelController:
    def __init__(self, step=4, hold_ms=2000):
        self.step = step
        self.hold_ms = hold_ms / 1000.0  # Convert to seconds
        self.mode = 'volume'  # 'volume' o 'select'
        self.audio = backend.AudioManager()
        self.running = False
        self.refresh_thread = None
        self.mute_down_at = None
        self.last_master_volume = None
        self.ui_callback = None  # Callback para notificar a la UI
        # Guardas para evitar eventos solapados y rebotes
        self.guard_until = 0.0  # tiempo hasta el que se ignoran up/down tras cambiar modo
        self.event_cooldown = 0.06  # segundos de debounce entre deltas
        self.last_delta_at = 0.0
        self.ignore_deltas_count = 0  # ignorar próximos deltas tras toggle

    def start(self):
        if self.running:
            return
        self.running = True
        try:
            self.audio.update_sessions()
        except Exception as e:
            print(f"[MEDIA-WHEEL] No se pudieron cargar sesiones: {e}")
        
        self.refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.refresh_thread.start()
        
        # Hook con keyboard library (como en Electron: suppress=True + return False)
        keyboard.hook(self._handle_keyboard, suppress=True)
        
        print("[MEDIA-WHEEL] Control de rueda multimedia activo (override nativo). Clic corto = alternar modo, mantener 2s = mute.")

    def stop(self):
        self.running = False
        try:
            keyboard.unhook_all()
        except:
            pass
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1)

    def _refresh_loop(self):
        while self.running:
            try:
                self.audio.update_sessions()
            except Exception as e:
                print(f"[MEDIA-WHEEL] Error refrescando sesiones: {e}")
            time.sleep(1)

    def _handle_keyboard(self, event):
        """Handler de teclado que suprime eventos multimedia (como Electron)"""
        if event.event_type != 'down':
            # Solo suprimir en key down; permitir key up pasar para evitar estados stuck
            if event.name == 'volume mute' and event.event_type == 'up':
                self._on_mute_up_internal()
            return True
        
        # Verificar si es una tecla multimedia primero
        if event.name not in ('volume up', 'volume down', 'volume mute'):
            return True  # No es una tecla multimedia, permitir pasar sin mostrar UI
        
        # Notificar a la UI para que se muestre (solo para teclas multimedia)
        if self.ui_callback:
            try:
                self.ui_callback()
            except:
                pass
        
        # Guardar volumen maestro actual
        self.last_master_volume = backend.get_master_volume()
        
        # Debounce y guard tras cambios de modo
        now = time.time()
        if event.name in ('volume up', 'volume down'):
            if self.ignore_deltas_count > 0:
                self.ignore_deltas_count -= 1
                return False
            if now < self.guard_until:
                return False
            if (now - self.last_delta_at) < self.event_cooldown:
                return False
            self.last_delta_at = now

        if event.name == 'volume up':
            self._handle_volume_change(self.step)
        elif event.name == 'volume down':
            self._handle_volume_change(-self.step)
        elif event.name == 'volume mute':
            self.mute_down_at = time.time()
        
        # Restaurar volumen maestro después de un breve delay (como en Electron)
        if self.last_master_volume is not None:
            time.sleep(0.05)
            current = backend.get_master_volume()
            if current != self.last_master_volume:
                backend.set_master_volume(self.last_master_volume)
        
        return False  # Suprimir evento nativo

    def _handle_volume_change(self, delta):
        if self.mode == 'select':
            state = self.audio.next_session() if delta > 0 else self.audio.prev_session()
            self._print_selection(state)
        else:
            session = self._current_session()
            if session:
                state = self.audio.change_volume(delta)
                self._print_volume(state)
            else:
                self._nudge_master(delta)

    def _on_mute_up_internal(self):
        if self.mute_down_at is None:
            self._toggle_mode()
            return
        
        held = time.time() - self.mute_down_at
        self.mute_down_at = None
        
        if held >= self.hold_ms:
            self._mute_current()
        else:
            self._toggle_mode()

    def _current_session(self):
        if not self.audio.sessions:
            return None
        idx = self.audio.selected_index
        if 0 <= idx < len(self.audio.sessions):
            return self.audio.sessions[idx]
        return None

    def _nudge_master(self, delta):
        current = backend.get_master()
        if current is None:
            return
        new_vol = max(0, min(100, current + delta))
        backend.set_master(new_vol)
        print(f"[MEDIA-WHEEL] Master {new_vol}%")

    def _toggle_mode(self):
        self.mode = 'select' if self.mode == 'volume' else 'volume'
        print(f"[MEDIA-WHEEL] Modo: {'selección' if self.mode == 'select' else 'volumen directo'}")
        # Tras cambiar modo, ignorar up/down por un corto periodo para evitar solapes
        self.guard_until = time.time() + 0.30
        # Reset del tiempo de último delta para cortar cadenas en curso
        self.last_delta_at = 0.0
        # Ignorar próximos 3 deltas de rueda para evitar cola de eventos
        self.ignore_deltas_count = 3

    def _mute_current(self):
        session = self._current_session()
        if session and session.get('_controls'):
            # Toggle mute: si está muteada, desmutea; si no, mutea
            target_mute = not session.get('isMuted', False)
            for control in session['_controls']:
                try:
                    control.SetMute(target_mute, None)
                except Exception:
                    pass
            session['isMuted'] = target_mute
            print(f"[MEDIA-WHEEL] {session['name']} {'silenciada' if target_mute else 'activa'}")
        else:
            try:
                backend.toggle_master_mute()
            except Exception:
                pass

    def _print_selection(self, state):
        try:
            sel = state['sessions'][state['selectedIndex']]
            print(f"[MEDIA-WHEEL] Selección: {sel['name']}")
        except Exception:
            pass

    def _print_volume(self, state):
        try:
            sel = state['sessions'][state['selectedIndex']]
            print(f"[MEDIA-WHEEL] {sel['name']} → {sel['volume']}% ({self.mode})")
        except Exception:
            pass


def start_media_wheel(step=4, hold_ms=2000):
    controller = MediaWheelController(step=step, hold_ms=hold_ms)
    controller.start()
    return controller
