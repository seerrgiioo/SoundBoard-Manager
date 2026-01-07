# Archivos de Idioma / Language Files

Esta carpeta contiene los archivos de traducción para SoundBoard Manager.

## Estructura

Cada archivo debe tener el formato `{código_idioma}.json` donde el código de idioma sigue el estándar ISO 639-1.

## Idiomas Disponibles

- `es.json` - Español
- `en.json` - English
- `fr.json` - Français
- `de.json` - Deutsch
- `it.json` - Italiano
- `pt.json` - Português
- `ja.json` - 日本語
- `zh.json` - 中文
- `ko.json` - 한국어
- `ru.json` - Русский

## Formato del Archivo

Cada archivo JSON debe contener las siguientes claves:

```json
{
  "mixer_title": "Título del mezclador",
  "no_apps": "Mensaje cuando no hay apps\ncon audio activo",
  "position_label": "Etiqueta de posición:",
  "language_label": "Etiqueta de idioma:",
  "cancel": "Cancelar",
  "save": "Guardar",
  "tray_show": "Mostrar",
  "tray_hide": "Ocultar",
  "tray_settings": "Configuración",
  "tray_exit": "Salir"
}
```

## Uso

La aplicación descargará automáticamente estos archivos desde GitHub la primera vez que se seleccione un idioma. Los archivos descargados se guardan en caché local para uso posterior.

## Contribuir

Para añadir un nuevo idioma:
1. Crea un archivo con el código de idioma apropiado (ej: `ar.json` para árabe)
2. Copia la estructura del archivo `es.json`
3. Traduce todas las cadenas de texto
4. Envía un Pull Request

## Ubicación en GitHub

Los archivos deben estar en: `https://raw.githubusercontent.com/tu-usuario/SoundManager/main/i18n/{codigo}.json`

Asegúrate de actualizar la URL en `src/i18n.py` si usas un repositorio diferente.
