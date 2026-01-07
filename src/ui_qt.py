#!/usr/bin/env python3
"""
SoundBoard Manager - UI Qt (PySide6)
Overlay minimalista, siempre encima, fondo translúcido y clic-through real.
- No capta el foco ni el ratón
- Se muestra con fade-in al recibir evento (media wheel)
- Auto-oculta tras un tiempo
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path
from typing import Optional, List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from . import backend

DARK_BG = QtGui.QColor("#1A1A1B")
DARK_CARD = QtGui.QColor("#1E1E20")
BORDER = QtGui.QColor("#2D2D2F")
WHITE = QtGui.QColor("#FFFFFF")
GREY = QtGui.QColor("#6E6E73")

CONFIG_DIR = Path.home() / 'AppData' / 'Local' / 'SoundBoard Manager'
CONFIG_FILE = CONFIG_DIR / 'settings.json'
DEFAULT_CONFIG = {
    'position': 'top-left',  # top-left, top-right, bottom-left, bottom-right
    'offset_x': 10,
    'offset_y': 10
}

def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"[CONFIG] Error saving: {e}")
        return False

class QtOverlay(QtWidgets.QWidget):
    requestShow = QtCore.Signal()
    requestHide = QtCore.Signal()
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = load_config()

        # Ventana sin borde, siempre arriba, tipo herramienta (oculta de taskbar)
        flags = (
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.NoDropShadowWindowHint
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # Ignorar el ratón: verdadero clic-through a través de Qt
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        # Refuerzo a nivel de ventana (Qt6): ignora input de forma global
        try:
            self.setWindowFlag(QtCore.Qt.WindowTransparentForInput, True)
        except Exception:
            pass

        # Geometría y opacidad
        self._apply_position_from_config()
        self.setWindowOpacity(0.0)

        # Datos de UI
        self._last_sessions: List[Tuple[str,int,bool]] = []

        # Timer de refresco
        self._refresh = QtCore.QTimer(self)
        self._refresh.setInterval(50)
        self._refresh.timeout.connect(self.update)
        self._refresh.start()

        # Auto-ocultar
        self._autohide_timer = QtCore.QTimer(self)
        self._autohide_timer.setSingleShot(True)
        self._autohide_timer.timeout.connect(self.hide_with_fade)

        # Animación
        self._anim = QtCore.QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        # Asegurar estilos de ventana en Win32 para passthrough (redundante a Qt pero robusto)
        self._apply_click_through_win32()

        # Conexiones thread-safe
        self.requestShow.connect(self.show_with_fade)
        self.requestHide.connect(self.hide_with_fade)

    def show_with_fade(self):
        if not self.isVisible():
            self.show()
        self._anim.stop()
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.95)
        self._anim.start()
        self._autohide_timer.start(3000)

    def hide_with_fade(self):
        self._anim.stop()
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._on_faded_out)
        self._anim.start()

    def _on_faded_out(self):
        if self.windowOpacity() <= 0.01:
            self.hide()
        try:
            self._anim.finished.disconnect(self._on_faded_out)
        except Exception:
            pass

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        try:
            p.setRenderHint(QtGui.QPainter.Antialiasing, True)

            # Panel base (sin fondo, solo transparente)
            rect = self.rect()
            panel = rect.adjusted(0, 0, 0, 0)

            # Logo/Icono a la izquierda del título (círculo blanco con speaker)
            logo_size = 32
            logo_rect = QtCore.QRect(panel.left()+15, panel.top()+14, logo_size, logo_size)
            p.setBrush(WHITE)
            p.setPen(QtCore.Qt.NoPen)
            # Círculo blanco
            p.drawEllipse(logo_rect)
            # Símbolo de altavoz (rectángulo + triángulo)
            p.setBrush(QtGui.QColor("#1A1A1B"))
            cx, cy = logo_rect.center().x(), logo_rect.center().y()
            # Rectángulo base del speaker
            p.drawRect(cx-8, cy-4, 5, 8)
            # Triángulo usando path
            path = QtGui.QPainterPath()
            path.moveTo(cx-3, cy-6)
            path.lineTo(cx+4, cy-10)
            path.lineTo(cx+4, cy+10)
            path.lineTo(cx-3, cy+6)
            path.closeSubpath()
            p.drawPath(path)
            # Ondas de sonido
            p.setPen(QtGui.QPen(QtGui.QColor("#1A1A1B"), 2))
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawArc(cx+5, cy-6, 6, 12, 300*16, 120*16)

            # Título (desplazado para dejar espacio al logo)
            title_rect = QtCore.QRect(panel.left()+55, panel.top()+18, panel.width()-100, 30)
            p.setPen(WHITE)
            title_font = QtGui.QFont("Segoe UI", 18, QtGui.QFont.Bold)
            p.setFont(title_font)
            p.drawText(title_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, "Mezclador de volumen")

            # Modo
            # mode_text = ""
            # try:
            #     mode_text = "Selección" if getattr(self.controller, 'mode', 'volume') == 'select' else "Volumen"
            # except Exception:
            #     mode_text = "Volumen"
            # mode_rect = QtCore.QRect(title_rect.right()-120, title_rect.top(), 120, title_rect.height())
            # small_font = QtGui.QFont("Segoe UI", 11)
            # p.setFont(small_font)
            # p.drawText(mode_rect, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, mode_text)

            # Sesiones
            sessions = []
            selected_idx = -1
            try:
                if self.controller and hasattr(self.controller, 'audio'):
                    sessions = list(self.controller.audio.sessions)
                    selected_idx = int(self.controller.audio.selected_index)
            except Exception:
                sessions = []

            y = title_rect.bottom() + 14
            item_h = 64
            left = panel.left() + 15
            right = panel.right() - 15
            for i, s in enumerate(sessions):
                name = str(s.get('name', ''))
                vol = int(s.get('volume', 0))
                is_sel = (i == selected_idx)

                # Card
                card_rect = QtCore.QRect(left, y, right-left, item_h)
                p.setBrush(DARK_CARD if is_sel else DARK_BG)
                pen = QtGui.QPen(WHITE if is_sel else BORDER)
                pen.setWidth(2 if is_sel else 1)
                p.setPen(pen)
                p.drawRoundedRect(card_rect, 10, 10)

                inner = card_rect.adjusted(14, 10, -14, -10)

                # Icono de la aplicación a la izquierda
                icon_size = 24
                icon_x = inner.left()
                icon_y = inner.top()
                icon_drawn = False
                try:
                    icon_data = s.get('icon')
                    # Si no hay icono en datos, intentar obtenerlo del proceso
                    if not icon_data:
                        try:
                            pid = s.get('pid')
                            if pid:
                                icon_data = backend.get_app_icon_base64(pid)
                        except Exception:
                            pass
                    
                    if icon_data:
                        # Convertir base64 a QPixmap
                        import base64
                        if isinstance(icon_data, str):
                            if icon_data.startswith('data:image/'):
                                b64_str = icon_data.split(',')[1]
                            else:
                                b64_str = icon_data
                            img_bytes = base64.b64decode(b64_str)
                            pixmap = QtGui.QPixmap()
                            if pixmap.loadFromData(img_bytes):
                                # Escalar a 24x24
                                pixmap = pixmap.scaled(icon_size, icon_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                                p.drawPixmap(icon_x, icon_y, pixmap)
                                icon_drawn = True
                except Exception:
                    pass

                # Nombre (desplazado si hay icono)
                text_left = icon_x + (icon_size + 8 if icon_drawn else 0)
                p.setPen(WHITE)
                p.setFont(QtGui.QFont("Segoe UI", 13, QtGui.QFont.Bold))
                p.drawText(QtCore.QRect(text_left, inner.top(), inner.width()-60-(text_left-inner.left()), 22),
                           QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, name)

                # Porcentaje o icono de mute
                is_muted = s.get('isMuted', False)
                if is_muted:
                    # Dibujar icono de mute (speaker con X)
                    mute_x = inner.right() - 50
                    mute_y = inner.top()
                    mute_size = 20
                    # Speaker
                    p.setBrush(WHITE)
                    p.setPen(QtCore.Qt.NoPen)
                    p.drawRect(mute_x, mute_y+6, 4, 8)
                    mpath = QtGui.QPainterPath()
                    mpath.moveTo(mute_x+4, mute_y+6)
                    mpath.lineTo(mute_x+10, mute_y+2)
                    mpath.lineTo(mute_x+10, mute_y+18)
                    mpath.lineTo(mute_x+4, mute_y+14)
                    mpath.closeSubpath()
                    p.drawPath(mpath)
                    # X roja
                    p.setPen(QtGui.QPen(QtGui.QColor("#FF4444"), 2))
                    p.drawLine(mute_x+12, mute_y+4, mute_x+18, mute_y+16)
                    p.drawLine(mute_x+12, mute_y+16, mute_x+18, mute_y+4)
                else:
                    p.setPen(WHITE)
                    p.setFont(QtGui.QFont("Segoe UI", 15, QtGui.QFont.Bold))
                    p.drawText(QtCore.QRect(inner.right()-60, inner.top(), 60, 22),
                               QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, f"{vol}%")

                # Barra de volumen
                bar_rect = QtCore.QRect(inner.left(), inner.bottom()-14, inner.width(), 10)
                # Fondo
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QColor("#2D2D2F"))
                p.drawRoundedRect(bar_rect, 5, 5)
                # Progreso
                prog_w = int(bar_rect.width() * max(0, min(100, vol))/100)
                prog_rect = QtCore.QRect(bar_rect.left(), bar_rect.top(), prog_w, bar_rect.height())
                p.setBrush(WHITE)
                p.drawRoundedRect(prog_rect, 5, 5)

                y += item_h + 10

            if not sessions:
                p.setPen(GREY)
                p.setFont(QtGui.QFont("Segoe UI", 13))
                p.drawText(panel, QtCore.Qt.AlignCenter, "No hay aplicaciones\ncon audio activo")
        finally:
            try:
                p.end()
            except Exception:
                pass

    def _apply_click_through_win32(self):
        # Refuerza el click-through en Windows con estilos mínimos, sin tocar Layered (Qt lo gestiona)
        try:
            import win32gui, win32con
            hwnd = int(self.winId())
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex |= (win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)
        except Exception:
            pass

    def _apply_position_from_config(self):
        """Calcula y aplica la posición desde la config"""
        width, height = 420, 520
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        pos = self.config.get('position', 'top-left')
        offset_x = self.config.get('offset_x', 10)
        offset_y = self.config.get('offset_y', 10)
        
        if pos == 'top-left':
            x, y = offset_x, offset_y
        elif pos == 'top-right':
            x, y = screen.width() - width - offset_x, offset_y
        elif pos == 'bottom-left':
            x, y = offset_x, screen.height() - height - offset_y
        elif pos == 'bottom-right':
            x, y = screen.width() - width - offset_x, screen.height() - height - offset_y
        else:
            x, y = offset_x, offset_y
        
        self.setGeometry(x, y, width, height)

    def show_settings(self):
        """Muestra diálogo de configuración"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)
            self._apply_position_from_config()

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("Configuración")
        self.setFixedSize(400, 250)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Título
        title = QtWidgets.QLabel("Configuración del Mezclador")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Posición
        pos_label = QtWidgets.QLabel("Posición en pantalla:")
        pos_label.setStyleSheet("font-size: 13px; color: white;")
        layout.addWidget(pos_label)
        
        self.pos_combo = QtWidgets.QComboBox()
        self.pos_combo.addItems(["Arriba Izquierda", "Arriba Derecha", "Abajo Izquierda", "Abajo Derecha"])
        positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
        current_pos = config.get('position', 'top-left')
        if current_pos in positions:
            self.pos_combo.setCurrentIndex(positions.index(current_pos))
        self.pos_combo.setStyleSheet("""
            QComboBox {
                background: #1E1E20;
                color: white;
                border: 2px solid #2D2D2F;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #1E1E20;
                color: white;
                selection-background-color: white;
                selection-color: #1A1A1B;
            }
        """)
        layout.addWidget(self.pos_combo)
        
        layout.addStretch()
        
        # Botones
        btn_layout = QtWidgets.QHBoxLayout()
        
        cancel_btn = QtWidgets.QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #2D2D2F;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #3D3D3F;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QtWidgets.QPushButton("Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #1A1A1B;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #E6E6E6;
            }
        """)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        # Estilo del diálogo
        self.setStyleSheet("QDialog { background: #1A1A1B; }")
    
    def get_config(self):
        positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
        self.config['position'] = positions[self.pos_combo.currentIndex()]
        return self.config


class SoundBoardUI:
    def __init__(self, root, controller=None):
        # root sin uso para compatibilidad
        self.app: Optional[QtWidgets.QApplication] = None
        self.win: Optional[QtOverlay] = None
        self.controller = controller

        # Crear QApplication si no existe
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        # Fuente por defecto
        self.app.setApplicationName("SoundBoard")

        self.win = QtOverlay(controller)

        # Conectar callback para mostrar overlay (thread-safe, desde keyboard thread)
        if self.controller:
            self.controller.ui_callback = lambda: self.win.requestShow.emit()

    def run(self):
        self.app.exec()
