const { app, BrowserWindow, Tray, Menu, ipcMain, screen } = require('electron');
const { spawn } = require('child_process');
const AutoLaunch = require('auto-launch');
const path = require('path');
const fs = require('fs');

let mainWindow;
let tray;
let positionWindow;
let hideTimer = null;
let backendProcess = null;
const settingsPath = path.join(app.getPath('userData'), 'settings.json');
const autoLauncher = new AutoLaunch({ name: 'SoundBoard Manager' });

// Sistema de i18n simplificado
let currentLanguage = 'en';
let translations = {};

function loadLanguage(lang) {
  try {
    const langPath = path.join(__dirname, 'i18n', `${lang}.json`);
    if (fs.existsSync(langPath)) {
      translations = JSON.parse(fs.readFileSync(langPath, 'utf8'));
      currentLanguage = lang;
      return translations;
    }
  } catch (error) {
    console.error('Error loading language:', error);
  }
  // Fallback a inglés
  const fallbackPath = path.join(__dirname, 'i18n', 'en.json');
  if (fs.existsSync(fallbackPath)) {
    translations = JSON.parse(fs.readFileSync(fallbackPath, 'utf8'));
    currentLanguage = 'en';
  }
  return translations;
}

function t(key) {
  return key.split('.').reduce((obj, k) => obj?.[k], translations) || key;
}

// Configuración
const defaultSettings = { x: null, y: null, width: 380, height: 240, opacity: 1, position: 'top-left', volumeDelta: 1, language: 'es' };

function loadSettings() {
  try {
    if (fs.existsSync(settingsPath)) {
      return { ...defaultSettings, ...JSON.parse(fs.readFileSync(settingsPath, 'utf8')) };
    }
  } catch (error) {
    console.error('Error loading settings:', error);
  }
  return { ...defaultSettings };
}

function saveSettings(settings) {
  try {
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
  } catch (error) {
    console.error('Error saving settings:', error);
  }
}

// Calcular posición basada en posición seleccionada
function getPositionCoordinates(positionKey) {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  const windowWidth = 380;
  const windowHeight = 240;
  const padding = 10;

  const positions = {
    'top-left': { x: padding, y: padding },
    'top-center': { x: (width - windowWidth) / 2, y: padding },
    'top-right': { x: width - windowWidth - padding, y: padding },
    'middle-left': { x: padding, y: (height - windowHeight) / 2 },
    'middle-center': { x: (width - windowWidth) / 2, y: (height - windowHeight) / 2 },
    'middle-right': { x: width - windowWidth - padding, y: (height - windowHeight) / 2 },
    'bottom-left': { x: padding, y: height - windowHeight - padding },
    'bottom-center': { x: (width - windowWidth) / 2, y: height - windowHeight - padding },
    'bottom-right': { x: width - windowWidth - padding, y: height - windowHeight - padding }
  };

  return positions[positionKey] || positions['top-left'];
}

function startBackend() {
  if (backendProcess) return;

  const exePath = app.isPackaged 
    ? path.join(process.resourcesPath, 'backend', 'SoundManagerBackend.exe')
    : path.join(__dirname, 'backend.py');
  
  const command = app.isPackaged ? exePath : 'py';
  const args = app.isPackaged ? [] : [exePath];
  
  try {
    backendProcess = spawn(command, args, { detached: true, stdio: 'ignore', cwd: __dirname });
    backendProcess.unref();
  } catch (err) {
    console.error('[BACKEND] Error:', err);
  }
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    try {
      backendProcess.kill();
    } catch (err) {
      console.error('[BACKEND] Error al detener:', err);
    }
  }
  backendProcess = null;
}

function createWindow() {
  const settings = loadSettings();
  
  mainWindow = new BrowserWindow({
    width: settings.width,
    height: settings.height,
    x: settings.x,
    y: settings.y,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // Forzar nivel máximo de prioridad (sobre juegos y apps pantalla completa)
  mainWindow.setAlwaysOnTop(true, 'screen-saver');
  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  mainWindow.loadFile(path.join(__dirname, 'ui', 'index.html'));
  
  // Posicionar ventana
  if (!settings.x || !settings.y) {
    const pos = getPositionCoordinates(settings.position || 'top-left');
    mainWindow.setPosition(pos.x, pos.y);
  }

  mainWindow.setOpacity(settings.opacity);
  mainWindow.setIgnoreMouseEvents(true, { forward: true });
  
  mainWindow.on('moved', () => {
    const [x, y] = mainWindow.getPosition();
    saveSettings({ ...loadSettings(), x, y });
  });
  
  ipcMain.on('show-window', () => {
    if (!positionWindow && mainWindow) {
      mainWindow.setAlwaysOnTop(true, 'screen-saver');
      mainWindow.show();
      mainWindow.moveTop();
      mainWindow.focus();
      mainWindow.webContents.send('remove-fadeout');
      resetHideTimer();
    }
  });
  
  ipcMain.on('hide-window', () => {
    if (mainWindow) mainWindow.hide();
  });
}

// Cambiar posición de la ventana
function setWindowPosition(positionKey) {
  if (!mainWindow) return;
  
  const pos = getPositionCoordinates(positionKey);
  mainWindow.setPosition(Math.round(pos.x), Math.round(pos.y));
  
  // Guardar la posición seleccionada en settings
  const settings = loadSettings();
  settings.position = positionKey;
  settings.x = Math.round(pos.x);
  settings.y = Math.round(pos.y);
  saveSettings(settings);
}

function resetHideTimer() {
  if (hideTimer) clearTimeout(hideTimer);
  
  hideTimer = setTimeout(() => {
    if (mainWindow?.isVisible()) {
      mainWindow.webContents.send('start-fadeout');
      setTimeout(() => mainWindow.hide(), 300);
    }
  }, 3000);
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'assets', 'icon.png'));
  
  const contextMenu = Menu.buildFromTemplate([
    { label: t('tray.settings'), click: () => createPositionWindow() },
    { type: 'separator' },
    { label: t('tray.exit'), click: () => app.quit() }
  ]);

  tray.setToolTip('SoundBoard Manager');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

function createPositionWindow() {
  if (positionWindow) {
    positionWindow.focus();
    return;
  }

  positionWindow = new BrowserWindow({
    width: 500,
    height: 700,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    backgroundMaterial: 'none',
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const configWindow = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: transparent;
          overflow: hidden;
          padding: 0;
          height: 100vh;
          width: 100vw;
        }
        
        .container {
          width: 100%;
          height: 100%;
          background: rgba(15, 15, 15, 0.85);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          transition: all 0.3s ease;
        }
        
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          background: transparent;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          transition: all 0.3s ease;
        }
        
        .header h1 {
          color: white;
          font-size: 14px;
          font-weight: 600;
        }
        
        .close-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 6px;
          background: transparent;
          color: rgba(255, 255, 255, 0.8);
          cursor: pointer;
          font-size: 16px;
          transition: all 0.2s;
        }
        
        .close-btn:hover {
          background: rgba(239, 68, 68, 0.9);
          color: white;
        }
        
        .content {
          flex: 1;
          overflow-y: scroll;
          overflow-x: hidden;
          padding: 16px;
          padding-right: 12px;
          scroll-behavior: smooth;
          min-height: 0;
        }
        
        .content::-webkit-scrollbar {
          width: 10px;
        }
        
        .content::-webkit-scrollbar-track {
          background: transparent;
          margin: 4px 0;
        }
        
        .content::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.3);
          border-radius: 5px;
          transition: background 0.3s ease;
          border: 2px solid transparent;
          background-clip: content-box;
        }
        
        .content::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.5);
          background-clip: content-box;
        }
        
        .section {
          margin-bottom: 20px;
        }
        
        .section-title {
          color: rgba(255, 255, 255, 0.8);
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 12px;
        }
        
        .position-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
          margin-bottom: 16px;
        }
        
        .position-btn {
          aspect-ratio: 1;
          border: 2px solid rgba(255, 255, 255, 0.2);
          background: rgba(255, 255, 255, 0.08);
          border-radius: 8px;
          cursor: pointer;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.8);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 4px;
          line-height: 1.2;
        }
        
        .position-btn:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.4);
          color: white;
          transform: translateY(-2px);
        }
        
        .position-btn.active {
          background: rgba(59, 130, 246, 0.5);
          border-color: rgba(59, 130, 246, 1);
          color: white;
          box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
          transform: scale(1.05);
        }
        
        .control-group {
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 12px;
          transition: all 0.3s ease;
        }
        
        .control-group:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.15);
        }
        
        .control-label {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .control-label-text {
          color: rgba(255, 255, 255, 0.9);
          font-size: 13px;
          font-weight: 500;
        }
        
        .control-value {
          color: rgba(255, 255, 255, 0.7);
          font-size: 12px;
        }
        
        .slider {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: rgba(255, 255, 255, 0.2);
          outline: none;
          -webkit-appearance: none;
          appearance: none;
          cursor: pointer;
          transition: background 0.3s ease;
        }
        
        .slider:hover {
          background: rgba(255, 255, 255, 0.3);
        }
        
        .slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.9);
          cursor: pointer;
          box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
          transition: all 0.2s ease;
        }
        
        .slider::-webkit-slider-thumb:hover {
          width: 16px;
          height: 16px;
          box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
        }
        
        .slider::-moz-range-thumb {
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.9);
          cursor: pointer;
          border: none;
          box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
          transition: all 0.2s ease;
        }
        
        .slider::-moz-range-thumb:hover {
          width: 16px;
          height: 16px;
          box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
        }
        
        .binds-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        
        .bind-input-group {
          display: flex;
          flex-direction: column;
        }
        
        .bind-label {
          color: rgba(255, 255, 255, 0.7);
          font-size: 11px;
          margin-bottom: 4px;
        }
        
        .bind-input {
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          padding: 6px 8px;
          color: rgba(255, 255, 255, 0.9);
          font-size: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .bind-input:hover {
          border-color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.1);
        }
        
        .bind-input.recording {
          background: rgba(59, 130, 246, 0.3);
          border-color: rgba(59, 130, 246, 0.8);
          color: white;
          box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
        }

        .reset-btn {
          margin-top: 10px;
          width: 100%;
          padding: 10px 12px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          background: rgba(255, 255, 255, 0.08);
          color: rgba(255, 255, 255, 0.9);
          font-size: 13px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .reset-btn:hover {
          background: rgba(59, 130, 246, 0.3);
          border-color: rgba(59, 130, 246, 0.8);
          color: white;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.35);
        }
        
        .language-select {
          width: 100%;
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          padding: 8px 10px;
          color: rgba(255, 255, 255, 0.9);
          font-size: 13px;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-top: 6px;
        }
        
        .language-select:hover {
          border-color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.1);
        }
        
        .language-select:focus {
          outline: none;
          border-color: rgba(59, 130, 246, 0.8);
          background: rgba(255, 255, 255, 0.12);
        }
        
        .language-select option {
          background: #1a1a1a;
          color: white;
          padding: 4px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1 id="configTitle">Configuración</h1>
          <button class="close-btn">✕</button>
        </div>
        
        <div class="content">
          <!-- Posiciones -->
          <div class="section">
            <div class="section-title">Posición</div>
            <div class="position-grid">
              <button class="position-btn" data-pos="top-left">Arriba<br>Izq</button>
              <button class="position-btn" data-pos="top-center">Arriba<br>Centro</button>
              <button class="position-btn" data-pos="top-right">Arriba<br>Der</button>
              
              <button class="position-btn" data-pos="middle-left">Medio<br>Izq</button>
              <button class="position-btn" data-pos="middle-center">Centro<br>Centro</button>
              <button class="position-btn" data-pos="middle-right">Medio<br>Der</button>
              
              <button class="position-btn" data-pos="bottom-left">Abajo<br>Izq</button>
              <button class="position-btn" data-pos="bottom-center">Abajo<br>Centro</button>
              <button class="position-btn" data-pos="bottom-right">Abajo<br>Der</button>
            </div>
          </div>
          
          <!-- Opacidad -->
          <div class="section">
            <div class="section-title">Apariencia</div>
            <div class="control-group">
              <div class="control-label">
                <span class="control-label-text">Opacidad</span>
                <span class="control-value" id="opacityValue">100%</span>
              </div>
              <input type="range" id="opacitySlider" class="slider" min="20" max="100" value="100">
            </div>
          </div>
          
          <!-- Volumen por defecto -->
          <div class="section">
            <div class="section-title">Volumen</div>
            <div class="control-group">
              <div class="control-label">
                <span class="control-label-text">Cambio de volumen</span>
                <span class="control-value" id="volumeValue">1%</span>
              </div>
              <input type="range" id="volumeSlider" class="slider" min="1" max="20" value="1">
            </div>
          </div>
          
          <!-- Binds -->
          <div class="section">
            <div class="section-title">Controles</div>
            <div class="binds-grid">
              <div class="bind-input-group">
                <label class="bind-label">Volumen Arriba</label>
                <input type="text" class="bind-input" id="volumeUp" readonly>
              </div>
              <div class="bind-input-group">
                <label class="bind-label">Volumen Abajo</label>
                <input type="text" class="bind-input" id="volumeDown" readonly>
              </div>
              <div class="bind-input-group">
                <label class="bind-label">Silenciar</label>
                <input type="text" class="bind-input" id="volumeMute" readonly>
              </div>
              <div class="bind-input-group">
                <label class="bind-label">Navegación</label>
                <input type="text" class="bind-input" id="navigation" readonly>
              </div>
            </div>
            <button class="reset-btn" id="resetBinds">Restablecer por defecto</button>
          </div>
          
          <!-- Idioma -->
          <div class="section">
            <div class="section-title">Preferencias</div>
            <div class="control-group">
              <div class="control-label">
                <span class="control-label-text">Idioma</span>
              </div>
              <select id="languageSelect" class="language-select">
                <option value="es">Español</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      
      <script>
        const { ipcRenderer } = require('electron');
        let currentPosition = 'top-left';
        let currentLanguage = 'es';
        let translations = {};
        let currentBinds = {
          volumeUp: 'Volume Up',
          volumeDown: 'Volume Down',
          volumeMute: 'Volume Mute',
          navigation: 'Mute'
        };
        
        // Recibir traducciones
        ipcRenderer.on('translations', (event, data) => {
          translations = data.translations;
          currentLanguage = data.language;
          updateUI();
        });
        
        // Actualizar UI con traducciones
        function updateUI() {
          const t = (key) => {
            const keys = key.split('.');
            let value = translations;
            for (const k of keys) {
              value = value?.[k];
            }
            return value || key;
          };
          
          document.getElementById('configTitle').textContent = t('config.title');
          document.querySelectorAll('.section-title').forEach((el, i) => {
            const titles = ['config.position', 'config.appearance', 'config.volume', 'config.controls', 'config.language'];
            if (titles[i]) el.textContent = t(titles[i]);
          });
          
          document.getElementById('languageSelect').value = currentLanguage;
          
          // Actualizar etiquetas de controles
          const labels = document.querySelectorAll('.control-label-text');
          if (labels[0]) labels[0].textContent = t('config.appearance');
          if (labels[1]) labels[1].textContent = t('config.volume.volumeDelta');
          if (labels[2]) labels[2].textContent = t('config.language');
        }
        
        // Cargar posición actual
        ipcRenderer.on('config-data', (event, data) => {
          currentPosition = data.position || 'top-left';
          currentLanguage = data.language || 'es';
          currentBinds = data.binds || currentBinds;
          document.querySelectorAll('.position-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.pos === currentPosition);
          });
          
          document.getElementById('opacitySlider').value = (data.opacity || 1) * 100;
          document.getElementById('opacityValue').textContent = Math.round((data.opacity || 1) * 100) + '%';
          
          document.getElementById('volumeSlider').value = data.volumeDelta || 1;
          document.getElementById('volumeValue').textContent = (data.volumeDelta || 1) + '%';
          
          document.getElementById('volumeUp').value = currentBinds.volumeUp;
          document.getElementById('volumeDown').value = currentBinds.volumeDown;
          document.getElementById('volumeMute').value = currentBinds.volumeMute;
          document.getElementById('navigation').value = currentBinds.navigation;
        });
        
        // Posiciones
        document.querySelectorAll('.position-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            currentPosition = btn.dataset.pos;
            document.querySelectorAll('.position-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            ipcRenderer.send('set-position', btn.dataset.pos);
          });
        });
        
        // Opacidad
        document.getElementById('opacitySlider').addEventListener('input', (e) => {
          const value = e.target.value / 100;
          document.getElementById('opacityValue').textContent = e.target.value + '%';
          ipcRenderer.send('set-opacity', value);
        });
        
        // Volumen
        document.getElementById('volumeSlider').addEventListener('input', (e) => {
          const value = parseInt(e.target.value);
          document.getElementById('volumeValue').textContent = value + '%';
          ipcRenderer.send('set-volume-delta', value);
        });

        // Binds - captura de teclas
        const bindIds = ['volumeUp', 'volumeDown', 'volumeMute', 'navigation'];
        let recordingInput = null;

        function formatKey(e) {
          const parts = [];
          if (e.ctrlKey) parts.push('Ctrl');
          if (e.altKey) parts.push('Alt');
          if (e.shiftKey) parts.push('Shift');
          if (e.metaKey) parts.push('Meta');
          parts.push(e.code || e.key);
          return parts.join('+');
        }

        function stopRecording() {
          if (!recordingInput) return;
          recordingInput.classList.remove('recording');
          recordingInput = null;
          window.removeEventListener('keydown', onKeyRecord, true);
        }

        function onKeyRecord(e) {
          e.preventDefault();
          e.stopPropagation();
          const value = formatKey(e);
          if (recordingInput) {
            recordingInput.value = value;
            currentBinds[recordingInput.id] = value;
            ipcRenderer.send('set-binds', currentBinds);
          }
          stopRecording();
        }

        bindIds.forEach((id) => {
          const input = document.getElementById(id);
          input.removeAttribute('readonly');
          input.addEventListener('focus', () => {
            recordingInput = input;
            input.classList.add('recording');
            window.addEventListener('keydown', onKeyRecord, true);
          });
          input.addEventListener('blur', stopRecording);
        });

        // Reset binds
        document.getElementById('resetBinds').addEventListener('click', () => {
          currentBinds = {
            volumeUp: 'Volume Up',
            volumeDown: 'Volume Down',
            volumeMute: 'Volume Mute',
            navigation: 'Mute'
          };
          bindIds.forEach((id) => {
            document.getElementById(id).value = currentBinds[id];
          });
          ipcRenderer.send('set-binds', currentBinds);
        });
        
        // Idioma
        document.getElementById('languageSelect').addEventListener('change', (e) => {
          const language = e.target.value;
          ipcRenderer.send('set-language', language);
        });
        
        // Cerrar
        document.querySelector('.close-btn').addEventListener('click', () => {
          ipcRenderer.send('close-position-window');
        });
        
        // Solicitar datos
        ipcRenderer.send('request-config-data');
      </script>
    </body>
    </html>
  `;

  positionWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(configWindow));

  positionWindow.on('closed', () => {
    positionWindow = null;
    // Permitir que el menú de volumen funcione nuevamente
    // (no lo mostramos automáticamente, solo permitimos que se muestre cuando se use la rueda)
  });

  positionWindow.show();
  
  // Ocultar el menú de volumen mientras está abierto el config
  if (mainWindow && mainWindow.isVisible()) {
    mainWindow.hide();
  }
}

// Handlers IPC
ipcMain.on('set-position', (event, positionKey) => setWindowPosition(positionKey));

ipcMain.on('set-opacity', (event, opacity) => {
  if (mainWindow) {
    mainWindow.setOpacity(opacity);
    saveSettings({ ...loadSettings(), opacity });
  }
});

ipcMain.on('set-volume-delta', (event, delta) => {
  saveSettings({ ...loadSettings(), volumeDelta: delta });
});

ipcMain.on('set-binds', (event, binds) => {
  saveSettings({ ...loadSettings(), binds });
});

ipcMain.on('request-config-data', (event) => {
  const settings = loadSettings();
  event.sender.send('config-data', {
    position: settings.position || 'top-left',
    opacity: settings.opacity || 1,
    volumeDelta: settings.volumeDelta || 1,
    language: settings.language || 'es',
    binds: settings.binds || {
      volumeUp: 'Volume Up',
      volumeDown: 'Volume Down',
      volumeMute: 'Volume Mute',
      navigation: 'Mute'
    }
  });
  
  event.sender.send('translations', {
    translations: translations,
    language: currentLanguage
  });
});

ipcMain.on('set-language', (event, language) => {
  loadLanguage(language);
  saveSettings({ ...loadSettings(), language });
  
  if (positionWindow) {
    positionWindow.webContents.send('translations', {
      translations: translations,
      language: currentLanguage
    });
  }
});

ipcMain.on('close-position-window', () => {
  if (positionWindow) positionWindow.close();
});

app.whenReady().then(() => {
  const settings = loadSettings();
  loadLanguage(settings.language || 'es');

  autoLauncher.isEnabled()
    .then((enabled) => {
      if (!enabled) autoLauncher.enable().catch(err => console.error('[AUTO-LAUNCH]', err));
    })
    .catch(err => console.error('[AUTO-LAUNCH]', err));

  startBackend();
  createWindow();
  createTray();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', stopBackend);
