#!/usr/bin/env python3
"""
Sistema de internacionalización (i18n)
Descarga archivos de idioma desde GitHub y los cachea localmente
"""
import json
import urllib.request
from pathlib import Path
from typing import Dict, Optional

# Directorio de cache para idiomas
CACHE_DIR = Path.home() / 'AppData' / 'Local' / 'SoundBoard Manager' / 'i18n'
GITHUB_REPO = "https://raw.githubusercontent.com/seerrgiioo/SoundBoard-Manager/refs/heads/main/i18n"

# Traducciones por defecto (español) si no se puede descargar
DEFAULT_TRANSLATIONS = {
    "es": {
        "mixer_title": "Mezclador de volumen",
        "no_apps": "No hay aplicaciones\ncon audio activo",
        "position_label": "Posición en pantalla:",
        "language_label": "Idioma / Language:",
        "cancel": "Cancelar",
        "save": "Guardar",
        "tray_show": "Mostrar",
        "tray_hide": "Ocultar",
        "tray_settings": "Configuración",
        "tray_exit": "Salir"
    },
    "en": {
        "mixer_title": "Volume Mixer",
        "no_apps": "No applications\nwith active audio",
        "position_label": "Screen position:",
        "language_label": "Language / Idioma:",
        "cancel": "Cancel",
        "save": "Save",
        "tray_show": "Show",
        "tray_hide": "Hide",
        "tray_settings": "Settings",
        "tray_exit": "Exit"
    }
}

class I18n:
    def __init__(self, language='es', github_repo=None):
        self.language = language
        self.github_repo = github_repo or GITHUB_REPO
        self.translations = {}
        self._load_language(language)
    
    def _load_language(self, lang_code: str):
        """Carga un idioma, primero desde cache, luego desde GitHub"""
        # Intentar cargar desde cache
        cache_file = CACHE_DIR / f"{lang_code}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                    return
            except Exception as e:
                print(f"[I18N] Error leyendo cache de {lang_code}: {e}")
        
        # Intentar descargar desde GitHub
        try:
            url = f"{self.github_repo}/{lang_code}.json"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read().decode('utf-8')
                self.translations = json.loads(data)
                # Guardar en cache
                self._save_to_cache(lang_code, self.translations)
                print(f"[I18N] Idioma {lang_code} descargado desde GitHub")
                return
        except Exception as e:
            print(f"[I18N] No se pudo descargar {lang_code} desde GitHub: {e}")
        
        # Fallback a traducciones por defecto
        if lang_code in DEFAULT_TRANSLATIONS:
            self.translations = DEFAULT_TRANSLATIONS[lang_code]
            print(f"[I18N] Usando traducciones por defecto para {lang_code}")
        else:
            # Usar español por defecto
            self.translations = DEFAULT_TRANSLATIONS['es']
            print(f"[I18N] Idioma {lang_code} no disponible, usando español")
    
    def _save_to_cache(self, lang_code: str, translations: Dict):
        """Guarda las traducciones en cache local"""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file = CACHE_DIR / f"{lang_code}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[I18N] Error guardando cache: {e}")
    
    def t(self, key: str, default: Optional[str] = None) -> str:
        """Traduce una clave (t = translate)"""
        return self.translations.get(key, default or key)
    
    def set_language(self, lang_code: str):
        """Cambia el idioma actual"""
        self.language = lang_code
        self._load_language(lang_code)

# Instancia global
_i18n_instance: Optional[I18n] = None

def get_i18n(language='es') -> I18n:
    """Obtiene la instancia global de i18n"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n(language)
    return _i18n_instance

def set_language(lang_code: str):
    """Cambia el idioma global"""
    global _i18n_instance
    if _i18n_instance:
        _i18n_instance.set_language(lang_code)
    else:
        _i18n_instance = I18n(lang_code)

def t(key: str, default: Optional[str] = None) -> str:
    """Atajo para traducir"""
    return get_i18n().t(key, default)
