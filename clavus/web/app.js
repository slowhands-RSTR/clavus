// Clavus Web Companion — CRUX family UI
let currentFilter = 'all';
let POLL_INTERVAL = 5000; // 5s auto-refresh

function $(id) { return document.getElementById(id); }

async function api(path, options = {}) {
  const url = '/api' + path;
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    console.error('API error:', url, resp.status, text);
    return { error: text };
  }
  return resp.json();
}

async function loadProject() {
  const data = await api('/project');
  if (data.error) {
    $('projectName').textContent = '⚠ ' + data.error;
    return;
  }
  $('projectName').textContent = data.name;
  $('connStatus').textContent = '⬤ connected';
  $('connStatus').className = 'connection-status';

  if (data.project) {
    const p = data.project;
    $('bpm').textContent = p.bpm || '—';
    $('timeSig').textContent = p.time_signature || '—';
    $('abletonVer').textContent = p.ableton_version || '—';
    $('trackCount').textContent = p.track_count || 0;

    // Tracks
    const trackList = $('trackList');
    if (p.tracks && p.tracks.length) {
      trackList.innerHTML = p.tracks.map(t => `
        <div class="track-item">
          <span class="track-dot" style="background:#${t.color.toString(16).padStart(6,'0')}"></span>
          <span class="track-name">${escapeHtml(t.name)}</span>
          <span class="track-type">${t.type}</span>
        </div>
      `).join('');
    } else {
      trackList.innerHTML = '<div class="empty-state">No tracks loaded</div>';
    }

    // Markers
    const markerList = $('markerList');
    if (p.markers && p.markers.length) {
      markerList.innerHTML = '<h3>Markers</h3>' + p.markers.map(m =>
        `<div class="marker-item"><span class="pos">${escapeHtml(m.time)}</span> ${escapeHtml(m.name)}</div>`
      ).join('');
    } else {
      markerList.innerHTML = '<h3>Markers</h3><div class="empty-state">No markers</div>';
    }
  }

  // History
  if (data.history && data.history.length) {
    $('snapshotCount').textContent = data.history.length;
    $('snapshotList').innerHTML = data.history.map(s => `
      <div class="snapshot-item ${s.is_head ? 'active' : 'noselect'}">
        <div>
          <span class="snap-hash">${s.is_head ? '➡ ' : ''}${s.hash}</span>
          <span class="snap-time">${s.time_str}</span>
        </div>
        <div class="snap-msg">${escapeHtml(s.message)}</div>
        <div class="snap-meta">${s.track_count} tracks @ ${s.bpm}bpm</div>
      </div>
    `).join('');
  } else {
    $('snapshotCount').textContent = '0';
    $('snapshotList').innerHTML = '<div class="empty-state">No snapshots</div>';
  }
}

async function loadCues() {
  const data = await api('/cues?pending_only=' + (currentFilter === 'pending' ? 'true' : 'false'));
  if (data.error) {
    $('cueList').innerHTML = '<div class="empty-state error">⚠ Failed to load cues</div>';
    return;
  }

  let cues = data.cues || [];
  if (currentFilter !== 'all' && currentFilter !== 'pending') {
    cues = cues.filter(c => c.status === currentFilter);
  }

  if (!cues.length) {
    $('cueList').innerHTML = '<div class="empty-state">No cues yet. Leave one above.</div>';
    return;
  }

  $('cueList').innerHTML = cues.map(c => `
    <div class="cue-card status-${c.status}">
      <div class="cue-card-header">
        <span class="cue-position">@${escapeHtml(c.position)}</span>
        <span class="cue-meta">${c.author} · ${c.time_str}</span>
      </div>
      <div class="cue-text">${escapeHtml(c.text)}</div>
      ${c.track_name ? `<div class="cue-meta" style="margin-top:2px">Track: ${escapeHtml(c.track_name)}</div>` : ''}
      ${(c.replies || []).map(r =>
        `<div class="cue-reply">
          <span class="reply-author">${escapeHtml(r.author)}:</span>
          <span class="reply-text">${escapeHtml(r.text)}</span>
        </div>`
      ).join('')}
      <div class="cue-actions">
        <span class="cue-status ${c.status}">${c.status}</span>
        ${c.status === 'pending' ? `
          <button class="cue-action-btn" onclick="showReply('${c.id}')">💬 Reply</button>
          <button class="cue-action-btn resolve" onclick="resolveCue('${c.id}')">✅ Resolve</button>
        ` : ''}
      </div>
      <div class="cue-reply-composer" id="reply-${c.id}" style="display:none">
        <input type="text" id="reply-text-${c.id}" placeholder="Type a reply..." onkeydown="if(event.key==='Enter')postReply('${c.id}')">
        <button onclick="postReply('${c.id}')">Send</button>
      </div>
    </div>
  `).join('');
}

function showReply(cueId) {
  const el = $('reply-' + cueId);
  el.style.display = el.style.display === 'none' ? 'flex' : 'none';
  if (el.style.display === 'flex') {
    $('reply-text-' + cueId).focus();
  }
}

async function postCue() {
  const text = $('cueText').value.trim();
  const position = $('cuePosition').value.trim() || '0.0.0';
  if (!text) return;

  $('cueSendBtn').textContent = '...';
  const result = await api('/cues', {
    method: 'POST',
    body: JSON.stringify({ text, position }),
  });
  $('cueSendBtn').textContent = '+ Cue';
  if (!result.error) {
    $('cueText').value = '';
    $('cuePosition').value = '0.0.0';
    loadCues();
  }
}

async function postReply(cueId) {
  const text = $('reply-text-' + cueId).value.trim();
  if (!text) return;

  await api('/cues/' + cueId + '/reply', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
  $('reply-text-' + cueId).value = '';
  $('reply-' + cueId).style.display = 'none';
  loadCues();
}

async function resolveCue(cueId) {
  await api('/cues/' + cueId + '/resolve', { method: 'POST' });
  loadCues();
}

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.filter-btn[data-filter="${filter}"]`).classList.add('active');
  loadCues();
}

async function loadAll() {
  await Promise.all([loadProject(), loadCues()]);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Keyboard shortcut: Enter to send cue
document.addEventListener('DOMContentLoaded', () => {
  $('cueText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      postCue();
    }
  });
  loadAll();
  setInterval(loadAll, POLL_INTERVAL);
});
