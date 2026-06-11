/* ==========================================
   POLLA MUNDIALISTA 2026
   Frontend Logic
   ========================================== */

// ==========================================
// STATE
// ==========================================
let currentFilter = 'all';
let matches = [];
let ranking = [];
let groups = {};
let userPredictions = {};

// ==========================================
// UTILITY FUNCTIONS
// ==========================================
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ==========================================
// API FUNCTIONS
// ==========================================
async function apiFetch(url, options = {}) {
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: 'Error de conexión' }));
            throw new Error(err.error || 'Error en la solicitud');
        }
        return await res.json();
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}

async function loadMatches() {
    const url = currentFilter === 'all' ? '/api/matches' : `/api/matches?group=${currentFilter}`;
    matches = await apiFetch(url);
    renderMatches();
    renderMyPredictions();
    if (document.getElementById('tab-admin')?.classList.contains('active')) {
        renderAdminPanel();
    }
}

async function loadRanking() {
    ranking = await apiFetch('/api/ranking');
    renderRanking();
}

async function loadGroups() {
    groups = await apiFetch('/api/groups');
    renderGroups();
}

async function loadMyPredictions() {
    const data = await apiFetch('/api/matches');
    userPredictions = {};
    data.forEach(m => {
        if (m.my_prediction) {
            userPredictions[m.id] = m.my_prediction;
        }
    });
}

// ==========================================
// PREDICTION MODAL
// ==========================================
function openPredictionModal(matchId) {
    const match = matches.find(m => m.id === matchId);
    if (!match) return;

    document.getElementById('matchIdInput').value = match.id;
    
    // Match detail
    document.getElementById('modalMatchDetail').innerHTML = `
        <div class="match-detail-teams">
            <div class="match-detail-team">
                <span class="flag">${match.local_flag}</span>
                <span class="name">${match.local_team}</span>
            </div>
            <span class="vs">VS</span>
            <div class="match-detail-team">
                <span class="flag">${match.visitor_flag}</span>
                <span class="name">${match.visitor_team}</span>
            </div>
        </div>
        <small>Grupo ${match.group_name} - ${match.match_date} ${match.match_time}</small>
        <small>${match.stadium}</small>
    `;

    document.getElementById('labelLocal').textContent = match.local_team;
    document.getElementById('labelVisitor').textContent = match.visitor_team;

    // Load existing prediction
    const existing = userPredictions[match.id];
    const deleteBtn = document.getElementById('deletePredictionBtn');
    if (existing) {
        document.getElementById('localScore').value = existing.local_score;
        document.getElementById('visitorScore').value = existing.visitor_score;
        deleteBtn.style.display = 'flex';
    } else {
        document.getElementById('localScore').value = '';
        document.getElementById('visitorScore').value = '';
        deleteBtn.style.display = 'none';
    }

    document.getElementById('predictionModal').classList.add('active');
}

function closePredictionModal() {
    document.getElementById('predictionModal').classList.remove('active');
}

// ==========================================
// RENDER FUNCTIONS
// ==========================================

function renderMatches() {
    const container = document.getElementById('matchesContainer');
    
    if (matches.length === 0) {
        container.innerHTML = '<div class="loading">No hay partidos disponibles</div>';
        return;
    }

    container.innerHTML = matches.map(m => {
        const hasPrediction = !!userPredictions[m.id];
        const isPlayed = m.is_played;
        const statusClass = isPlayed ? 'played' : 'pending';
        const statusText = isPlayed ? 'Jugado' : 'Pendiente';
        
        let scoreHtml = '';
        if (isPlayed) {
            scoreHtml = `
                <div class="match-score-display">${m.local_score} - ${m.visitor_score}</div>
            `;
        } else {
            scoreHtml = `<span class="match-vs-display">VS</span>`;
        }

        let predictionBadge = '';
        if (hasPrediction) {
            const pred = userPredictions[m.id];
            if (isPlayed) {
                const pointsClass = pred.puntos > 0 ? 'hit' : 'miss';
                predictionBadge = `
                    <div class="match-prediction-badge">
                        <i class="fas fa-star"></i> ${pred.puntos} pts
                    </div>
                `;
            } else {
                predictionBadge = `
                    <div class="match-prediction-badge">
                        <i class="fas fa-check"></i> ${pred.local_score}-${pred.visitor_score}
                    </div>
                `;
            }
        }

        return `
            <div class="match-card" onclick="${!isPlayed ? `openPredictionModal(${m.id})` : ''}">
                <div class="match-card-header">
                    <span class="match-group-badge">Grupo ${m.group_name}</span>
                    <span class="match-status ${statusClass}">${statusText}</span>
                </div>
                <div class="match-body">
                    <div class="match-team">
                        <span class="flag">${m.local_flag}</span>
                        <span class="name">${m.local_team}</span>
                    </div>
                    ${scoreHtml}
                    <div class="match-team match-team-right">
                        <span class="name">${m.visitor_team}</span>
                        <span class="flag">${m.visitor_flag}</span>
                    </div>
                </div>
                <div class="match-footer">
                    <span>${m.match_date} - ${m.match_time}</span>
                    ${predictionBadge}
                </div>
            </div>
        `;
    }).join('');
}

function renderRanking() {
    const container = document.getElementById('rankingContainer');
    
    if (ranking.length === 0) {
        container.innerHTML = '<div class="loading">No hay participantes aún</div>';
        return;
    }

    container.innerHTML = `
        <div class="ranking-header">
            <span>Pos</span>
            <span>Participante</span>
            <span style="text-align:center">Pts</span>
            <span style="text-align:center">Aciertos</span>
            <span style="text-align:center">Exactos</span>
        </div>
        ${ranking.map((r, i) => {
            const posClass = i === 0 ? 'position-1' : i === 1 ? 'position-2' : i === 2 ? 'position-3' : '';
            return `
                <div class="ranking-row">
                    <span class="ranking-position ${posClass}">${r.position}</span>
                    <div class="ranking-user">
                        <img src="${r.photo}" alt="" class="ranking-avatar" onerror="this.style.display='none'">
                        <span class="ranking-name">${r.name} ${r.is_admin ? '👑' : ''}</span>
                    </div>
                    <span class="ranking-stat points">${r.total_points}</span>
                    <span class="ranking-stat">${r.predictions_count}</span>
                    <span class="ranking-stat">${r.correct_exact}</span>
                </div>
            `;
        }).join('')}
    `;
}

function renderGroups() {
    const container = document.getElementById('groupsContainer');
    const groupKeys = Object.keys(groups);
    
    if (groupKeys.length === 0) {
        container.innerHTML = '<div class="loading">No hay datos de grupos disponibles</div>';
        return;
    }

    container.innerHTML = `
        <div class="groups-grid">
            ${groupKeys.map(key => {
                const teams = groups[key];
                return `
                    <div class="group-card">
                        <div class="group-title">Grupo ${key}</div>
                        <table class="group-table">
                            <thead>
                                <tr>
                                    <th>Equipo</th>
                                    <th>PJ</th>
                                    <th>G</th>
                                    <th>E</th>
                                    <th>P</th>
                                    <th>GF</th>
                                    <th>GC</th>
                                    <th>Pts</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${teams.map(t => `
                                    <tr>
                                        <td>
                                            <div class="team-cell">
                                                <span class="team-flag">${t.flag}</span>
                                                <span>${t.name}</span>
                                            </div>
                                        </td>
                                        <td>${t.pj}</td>
                                        <td>${t.pg}</td>
                                        <td>${t.pe}</td>
                                        <td>${t.pp}</td>
                                        <td>${t.gf}</td>
                                        <td>${t.gc}</td>
                                        <td><strong>${t.pts}</strong></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderMyPredictions() {
    const container = document.getElementById('myPredictionsContainer');
    const myPreds = matches.filter(m => userPredictions[m.id]);
    
    if (myPreds.length === 0) {
        container.innerHTML = '<div class="loading">No has hecho ningún pronóstico aún. Ve a la sección Partidos para pronosticar.</div>';
        return;
    }

    container.innerHTML = `
        <div class="predictions-list">
            ${myPreds.map(m => {
                const pred = userPredictions[m.id];
                const isPlayed = m.is_played;
                let pointsHtml = '';
                if (isPlayed) {
                    const cls = pred.puntos > 0 ? 'hit' : 'miss';
                    const icon = pred.puntos > 0 ? 'fa-check-circle' : 'fa-times-circle';
                    pointsHtml = `
                        <div class="prediction-points ${cls}">
                            <i class="fas ${icon}"></i>
                            <span>${pred.puntos} pts</span>
                        </div>
                    `;
                } else {
                    pointsHtml = `<div class="prediction-points"><i class="fas fa-clock"></i> Pendiente</div>`;
                }

                return `
                    <div class="prediction-item" onclick="${!isPlayed ? `openPredictionModal(${m.id})` : ''}">
                        <div class="prediction-match">
                            <div class="prediction-teams">
                                <span>${m.local_flag} ${m.local_team}</span>
                                <span class="prediction-score">${pred.local_score} - ${pred.visitor_score}</span>
                                <span>${m.visitor_team} ${m.visitor_flag}</span>
                            </div>
                            <small>Grupo ${m.group_name} - ${m.match_date}</small>
                        </div>
                        ${pointsHtml}
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderAdminPanel() {
    const container = document.getElementById('adminContainer');
    
    container.innerHTML = `
        <div class="admin-list">
            ${matches.filter(m => !m.is_played).map(m => `
                <div class="admin-item">
                    <div class="admin-match-info">
                        <strong>${m.local_flag} ${m.local_team} vs ${m.visitor_team} ${m.visitor_flag}</strong>
                        <br>
                        <small>Grupo ${m.group_name} - ${m.match_date} ${m.match_time}</small>
                    </div>
                    <div class="admin-score-form" data-match-id="${m.id}">
                        <input type="number" class="admin-input" placeholder="0" min="0" max="20" id="admin-local-${m.id}">
                        <span style="color:var(--text-muted);font-weight:700">:</span>
                        <input type="number" class="admin-input" placeholder="0" min="0" max="20" id="admin-visitor-${m.id}">
                        <button class="btn btn-success" onclick="submitResult(${m.id})">
                            <i class="fas fa-check"></i> Guardar
                        </button>
                    </div>
                </div>
            `).join('')}
            ${matches.filter(m => m.is_played).length > 0 ? `
                <div style="margin-top:20px">
                    <h3 style="color:var(--accent-green);font-size:0.9rem;margin-bottom:10px">
                        <i class="fas fa-check-circle"></i> Partidos con resultado cargado
                    </h3>
                    ${matches.filter(m => m.is_played).map(m => `
                        <div class="admin-item" style="opacity:0.6">
                            <div class="admin-match-info">
                                <strong>${m.local_flag} ${m.local_team} ${m.local_score} - ${m.visitor_score} ${m.visitor_team} ${m.visitor_flag}</strong>
                                <br>
                                <small>Grupo ${m.group_name} - ${m.match_date}</small>
                            </div>
                            <span style="color:var(--accent-green)"><i class="fas fa-check"></i> Completado</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// ==========================================
// EVENT HANDLERS
// ==========================================

// Tab navigation
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        const tabName = this.getAttribute('data-tab');
        document.getElementById(`tab-${tabName}`).classList.add('active');
        
        // Lazy load
        if (tabName === 'ranking') loadRanking();
        if (tabName === 'grupos') loadGroups();
        if (tabName === 'admin') renderAdminPanel();
        if (tabName === 'mispredictions') renderMyPredictions();
    });
});

// Filter tabs
document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        currentFilter = this.getAttribute('data-filter');
        loadMatches();
    });
});

// Prediction form
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const matchId = parseInt(document.getElementById('matchIdInput').value);
    const localScore = parseInt(document.getElementById('localScore').value);
    const visitorScore = parseInt(document.getElementById('visitorScore').value);
    
    if (isNaN(localScore) || isNaN(visitorScore)) {
        showToast('Ingresa ambos marcadores', 'error');
        return;
    }
    
    try {
        await apiFetch('/api/predictions', {
            method: 'POST',
            body: JSON.stringify({ match_id: matchId, local_score: localScore, visitor_score: visitorScore })
        });
        
        showToast('¡Pronóstico guardado!');
        closePredictionModal();
        await loadMyPredictions();
        renderMatches();
        renderMyPredictions();
    } catch (err) {
        showToast('Error al guardar pronóstico', 'error');
    }
});

// Delete prediction
document.getElementById('deletePredictionBtn').addEventListener('click', async function() {
    const matchId = parseInt(document.getElementById('matchIdInput').value);
    
    if (!confirm('¿Eliminar este pronóstico?')) return;
    
    try {
        await apiFetch(`/api/predictions/${matchId}`, { method: 'DELETE' });
        showToast('Pronóstico eliminado', 'info');
        closePredictionModal();
        await loadMyPredictions();
        renderMatches();
        renderMyPredictions();
    } catch (err) {
        showToast('Error al eliminar pronóstico', 'error');
    }
});

// Modal close
document.getElementById('modalClose').addEventListener('click', closePredictionModal);
document.getElementById('predictionModal').addEventListener('click', function(e) {
    if (e.target === this) closePredictionModal();
});

// ==========================================
// ADMIN FUNCTIONS
// ==========================================
async function submitResult(matchId) {
    const localScore = parseInt(document.getElementById(`admin-local-${matchId}`).value);
    const visitorScore = parseInt(document.getElementById(`admin-visitor-${matchId}`).value);
    
    if (isNaN(localScore) || isNaN(visitorScore)) {
        showToast('Ingresa ambos marcadores', 'error');
        return;
    }
    
    try {
        await apiFetch(`/api/admin/matches/${matchId}/result`, {
            method: 'POST',
            body: JSON.stringify({ local_score: localScore, visitor_score: visitorScore })
        });
        
        showToast('¡Resultado guardado! Puntuaciones recalculadas.');
        await loadMatches();
        renderAdminPanel();
        loadRanking();
    } catch (err) {
        showToast('Error al guardar resultado', 'error');
    }
}

// ==========================================
// INIT
// ==========================================
async function init() {
    // Load data
    await Promise.all([
        loadMyPredictions(),
        loadMatches()
    ]);
}

document.addEventListener('DOMContentLoaded', init);