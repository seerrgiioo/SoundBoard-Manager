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
  if (volume === 0) return '🔇';
  if (volume < 33) return '🔈';
  if (volume < 66) return '🔉';
  return '🔊';
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
