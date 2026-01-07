// Conexión WebSocket optimizada
const { ipcRenderer } = require('electron');
let ws;
let reconnectTimer;
let lastStateJson = '';

function connect() {
  ws = new WebSocket('ws://localhost:8765');
  ws.onopen = () => requestState();
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'state') {
      renderAppsFromState(message.data);
    } else if (message.type === 'show') {
      ipcRenderer.send('show-window');
    }
  };
  ws.onclose = () => {
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(connect, 2000);
  };
}

function requestState() {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'get_state' }));
  }
}

function getVolumeIcon(volume) {
  // Lucide-style inline SVG (stroke icons)
  const common = 'width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';

  const speaker = '<path d="M11 5 L7.5 8 H5 v8 h2.5 L11 19 V5 Z" />';
  const wave1 = '<path d="M15 9 a3 3 0 0 1 0 6" />';
  const wave2 = '<path d="M17 7 a5 5 0 0 1 0 10" />';
  const wave3 = '<path d="M19 5 a7 7 0 0 1 0 14" />';
  const cross = '<line x1="19" y1="9" x2="23" y2="13" /><line x1="23" y1="9" x2="19" y2="13" />';

  if (volume === 0) {
    // volume-x (mute)
    return `<svg ${common}>${speaker}${cross}</svg>`;
  }
  if (volume < 33) {
    // volume-1 (low)
    return `<svg ${common}>${speaker}${wave1}</svg>`;
  }
  if (volume < 66) {
    // volume-2 (medium)
    return `<svg ${common}>${speaker}${wave1}${wave2}</svg>`;
  }
  // volume (high)
  return `<svg ${common}>${speaker}${wave1}${wave2}${wave3}</svg>`;
}

function renderAppsFromState(state) {
  const stateJson = JSON.stringify(state);
  if (stateJson === lastStateJson) return;
  lastStateJson = stateJson;

  const container = document.getElementById('appsContainer');
  container.innerHTML = '';

  const sessions = state.sessions || [];
  sessions.forEach((session, index) => {
    const appCard = document.createElement('div');
    appCard.className = `app-card ${session.isSelected ? 'active' : ''}`;
    appCard.id = `app-card-${index}`;

    const volumeIcon = getVolumeIcon(session.volume);
    const iconHtml = (session.icon?.startsWith('data:image') || session.icon?.endsWith('.png'))
      ? `<img src="${session.icon}" class="app-icon" style="width:32px;height:32px;object-fit:contain" />`
      : `<div class="app-icon">${session.icon || '🎵'}</div>`;

    appCard.innerHTML = `
      <div class="app-header">
        ${iconHtml}
        <div class="app-info">
          <h3 class="app-name">${session.name}</h3>
        </div>
        ${session.isSelected ? '<span class="active-badge">Activo</span>' : ''}
      </div>
      <div class="volume-control">
        <button class="mute-btn" onclick="event.stopPropagation();">${volumeIcon}</button>
        <div class="slider-container">
          <div class="volume-track">
            <div class="volume-fill" style="width: ${session.volume}%"></div>
          </div>
          <input type="range" min="0" max="100" value="${session.volume}" class="volume-slider" disabled />
        </div>
        <span class="volume-text">${session.volume}%</span>
      </div>
    `;
    container.appendChild(appCard);
  });

  // Scroll a la tarjeta activa
  setTimeout(() => {
    const activeCard = container.querySelector('.app-card.active');
    if (activeCard) {
      activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, 50);
}

// Animaciones
ipcRenderer.on('start-fadeout', () => {
  document.querySelector('.glass-window')?.classList.add('fadeout');
});

ipcRenderer.on('remove-fadeout', () => {
  document.querySelector('.glass-window')?.classList.remove('fadeout');
});

// Iniciar
connect();
