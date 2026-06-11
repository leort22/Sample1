import os
import json
from datetime import datetime

# Allow HTTP for local development (OAuth requires HTTPS in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from dotenv import load_dotenv

from models import db, User, Match, Prediction

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///polla.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions BEFORE auth
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Google Auth Blueprint
# Flask-Dance creates routes:
#   /login/google          -> redirects to Google
#   /login/google/authorized -> callback from Google
# In Google Cloud Console:
#   Authorized redirect URIs: http://localhost:5000/login/google/authorized
google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=["openid", "email", "profile"],
    redirect_to="dashboard",
)
app.register_blueprint(google_bp, url_prefix="/login")

# Auto-create user on Google login
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not google.authorized:
        return False
    
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return False
    
    info = resp.json()
    google_id = info['id']
    email = info['email']
    name = info.get('name', email.split('@')[0])
    photo = info.get('picture', '')
    
    # Find or create user
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        # First user becomes admin
        is_admin = User.query.count() == 0
        user = User(google_id=google_id, name=name, email=email, photo=photo, is_admin=is_admin)
        db.session.add(user)
    else:
        # Update info
        user.name = name
        user.photo = photo
    
    db.session.commit()
    login_user(user)
    
    return False

# ==========================================
# SEED DATA - Partidos del Mundial 2026
# ==========================================
MATCHES_DATA = [
    # Grupo A
    {"local": "México", "local_flag": "🇲🇽", "visitor": "Canadá", "visitor_flag": "🇨🇦", "grupo": "A", "fecha": "2026-06-11", "hora": "15:00", "estadio": "Estadio Azteca"},
    {"local": "Italia", "local_flag": "🇮🇹", "visitor": "Corea del Sur", "visitor_flag": "🇰🇷", "grupo": "A", "fecha": "2026-06-11", "hora": "18:00", "estadio": "Estadio Monumental"},
    {"local": "México", "local_flag": "🇲🇽", "visitor": "Italia", "visitor_flag": "🇮🇹", "grupo": "A", "fecha": "2026-06-16", "hora": "15:00", "estadio": "Estadio Azteca"},
    {"local": "Canadá", "local_flag": "🇨🇦", "visitor": "Corea del Sur", "visitor_flag": "🇰🇷", "grupo": "A", "fecha": "2026-06-16", "hora": "18:00", "estadio": "Estadio Nacional"},
    {"local": "México", "local_flag": "🇲🇽", "visitor": "Corea del Sur", "visitor_flag": "🇰🇷", "grupo": "A", "fecha": "2026-06-21", "hora": "15:00", "estadio": "Estadio Azteca"},
    {"local": "Canadá", "local_flag": "🇨🇦", "visitor": "Italia", "visitor_flag": "🇮🇹", "grupo": "A", "fecha": "2026-06-21", "hora": "15:00", "estadio": "Estadio Nacional"},
    
    # Grupo B
    {"local": "Brasil", "local_flag": "🇧🇷", "visitor": "Portugal", "visitor_flag": "🇵🇹", "grupo": "B", "fecha": "2026-06-12", "hora": "16:00", "estadio": "Estadio Maracaná"},
    {"local": "Japón", "local_flag": "🇯🇵", "visitor": "Arabia Saudita", "visitor_flag": "🇸🇦", "grupo": "B", "fecha": "2026-06-12", "hora": "19:00", "estadio": "Estadio do Morumbi"},
    {"local": "Brasil", "local_flag": "🇧🇷", "visitor": "Japón", "visitor_flag": "🇯🇵", "grupo": "B", "fecha": "2026-06-17", "hora": "16:00", "estadio": "Estadio Maracaná"},
    {"local": "Portugal", "local_flag": "🇵🇹", "visitor": "Arabia Saudita", "visitor_flag": "🇸🇦", "grupo": "B", "fecha": "2026-06-17", "hora": "19:00", "estadio": "Estadio do Morumbi"},
    {"local": "Brasil", "local_flag": "🇧🇷", "visitor": "Arabia Saudita", "visitor_flag": "🇸🇦", "grupo": "B", "fecha": "2026-06-22", "hora": "16:00", "estadio": "Estadio Maracaná"},
    {"local": "Portugal", "local_flag": "🇵🇹", "visitor": "Japón", "visitor_flag": "🇯🇵", "grupo": "B", "fecha": "2026-06-22", "hora": "16:00", "estadio": "Estadio do Morumbi"},
    
    # Grupo C
    {"local": "Francia", "local_flag": "🇫🇷", "visitor": "Argentina", "visitor_flag": "🇦🇷", "grupo": "C", "fecha": "2026-06-13", "hora": "14:00", "estadio": "Estadio Monumental"},
    {"local": "Inglaterra", "local_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "visitor": "Senegal", "visitor_flag": "🇸🇳", "grupo": "C", "fecha": "2026-06-13", "hora": "17:00", "estadio": "Estadio Nacional"},
    {"local": "Francia", "local_flag": "🇫🇷", "visitor": "Inglaterra", "visitor_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "grupo": "C", "fecha": "2026-06-18", "hora": "14:00", "estadio": "Estadio Monumental"},
    {"local": "Argentina", "local_flag": "🇦🇷", "visitor": "Senegal", "visitor_flag": "🇸🇳", "grupo": "C", "fecha": "2026-06-18", "hora": "17:00", "estadio": "Estadio Nacional"},
    {"local": "Francia", "local_flag": "🇫🇷", "visitor": "Senegal", "visitor_flag": "🇸🇳", "grupo": "C", "fecha": "2026-06-23", "hora": "14:00", "estadio": "Estadio Monumental"},
    {"local": "Argentina", "local_flag": "🇦🇷", "visitor": "Inglaterra", "visitor_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "grupo": "C", "fecha": "2026-06-23", "hora": "14:00", "estadio": "Estadio Nacional"},
    
    # Grupo D
    {"local": "Alemania", "local_flag": "🇩🇪", "visitor": "España", "visitor_flag": "🇪🇸", "grupo": "D", "fecha": "2026-06-14", "hora": "15:00", "estadio": "Estadio Olímpico"},
    {"local": "Países Bajos", "local_flag": "🇳🇱", "visitor": "Uruguay", "visitor_flag": "🇺🇾", "grupo": "D", "fecha": "2026-06-14", "hora": "18:00", "estadio": "Estadio do Morumbi"},
    {"local": "Alemania", "local_flag": "🇩🇪", "visitor": "Países Bajos", "visitor_flag": "🇳🇱", "grupo": "D", "fecha": "2026-06-19", "hora": "15:00", "estadio": "Estadio Olímpico"},
    {"local": "España", "local_flag": "🇪🇸", "visitor": "Uruguay", "visitor_flag": "🇺🇾", "grupo": "D", "fecha": "2026-06-19", "hora": "18:00", "estadio": "Estadio Nacional"},
    {"local": "Alemania", "local_flag": "🇩🇪", "visitor": "Uruguay", "visitor_flag": "🇺🇾", "grupo": "D", "fecha": "2026-06-24", "hora": "15:00", "estadio": "Estadio Olímpico"},
    {"local": "España", "local_flag": "🇪🇸", "visitor": "Países Bajos", "visitor_flag": "🇳🇱", "grupo": "D", "fecha": "2026-06-24", "hora": "15:00", "estadio": "Estadio Nacional"},
]

def seed_matches():
    """Insert matches if they don't exist"""
    if Match.query.first():
        return  # Already seeded
    
    for m in MATCHES_DATA:
        match = Match(
            local_team=m["local"],
            visitor_team=m["visitor"],
            local_flag=m["local_flag"],
            visitor_flag=m["visitor_flag"],
            group_name=m["grupo"],
            match_date=m["fecha"],
            match_time=m["hora"],
            stadium=m["estadio"],
        )
        db.session.add(match)
    db.session.commit()

# ==========================================
# SCORING SYSTEM
# ==========================================
def calculate_points(pred_local, pred_visitor, real_local, real_visitor):
    """
    Puntuación:
    - 7 pts: Marcador exacto
    - 3 pts: Goles de un equipo correctos (cada uno)
    - 2 pts: Ganador/Empate correcto
    - Se toma el puntaje MÁS ALTO
    """
    if pred_local == real_local and pred_visitor == real_visitor:
        return 7  # Marcador exacto
    
    # Check if both goals correct but not exact score (e.g. 0-0 vs 0-0 is exact score)
    if pred_local == real_local and pred_visitor != real_visitor:
        return 3  # Goles local correctos
    if pred_visitor == real_visitor and pred_local != real_local:
        return 3  # Goles visitante correctos
    
    # Ganador o empate correcto
    real_diff = real_local - real_visitor
    pred_diff = pred_local - pred_visitor
    
    # Same winner (both teams same score diff sign)
    if (real_diff > 0 and pred_diff > 0) or (real_diff < 0 and pred_diff < 0):
        return 2  # Ganador correcto
    
    # Both teams equal (draw)
    if real_diff == 0 and pred_diff == 0:
        return 2  # Empate correcto
    
    return 0  # Nada correcto

def recalculate_all_points():
    """Recalculate points for all predictions when results are updated"""
    predictions = Prediction.query.all()
    for pred in predictions:
        match = pred.match
        if match.is_played and match.local_score is not None and match.visitor_score is not None:
            pred.puntos = calculate_points(
                pred.local_score, pred.visitor_score,
                match.local_score, match.visitor_score
            )
    db.session.commit()

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

# ==========================================
# API - Matches
# ==========================================

@app.route('/api/matches')
def api_matches():
    group = request.args.get('group')
    query = Match.query.order_by(Match.match_date, Match.match_time)
    if group:
        query = query.filter_by(group_name=group)
    matches = query.all()
    
    result = []
    for m in matches:
        user_pred = Prediction.query.filter_by(user_id=current_user.id, match_id=m.id).first() if current_user.is_authenticated else None
        
        result.append({
            'id': m.id,
            'local_team': m.local_team,
            'visitor_team': m.visitor_team,
            'local_flag': m.local_flag,
            'visitor_flag': m.visitor_flag,
            'group_name': m.group_name,
            'match_date': m.match_date,
            'match_time': m.match_time,
            'stadium': m.stadium,
            'local_score': m.local_score,
            'visitor_score': m.visitor_score,
            'is_played': m.is_played,
            'my_prediction': {
                'local_score': user_pred.local_score,
                'visitor_score': user_pred.visitor_score,
                'puntos': user_pred.puntos
            } if user_pred else None
        })
    
    return jsonify(result)

@app.route('/api/matches/<int:match_id>', methods=['GET'])
def api_match_detail(match_id):
    match = Match.query.get_or_404(match_id)
    user_pred = Prediction.query.filter_by(user_id=current_user.id, match_id=match.id).first() if current_user.is_authenticated else None
    
    return jsonify({
        'id': match.id,
        'local_team': match.local_team,
        'visitor_team': match.visitor_team,
        'local_flag': match.local_flag,
        'visitor_flag': match.visitor_flag,
        'group_name': match.group_name,
        'match_date': match.match_date,
        'match_time': match.match_time,
        'stadium': match.stadium,
        'local_score': match.local_score,
        'visitor_score': match.visitor_score,
        'is_played': match.is_played,
        'my_prediction': {
            'local_score': user_pred.local_score,
            'visitor_score': user_pred.visitor_score,
            'puntos': user_pred.puntos
        } if user_pred else None
    })

# ==========================================
# API - Predictions
# ==========================================

@app.route('/api/predictions', methods=['POST'])
@login_required
def save_prediction():
    data = request.json
    match_id = data.get('match_id')
    local_score = data.get('local_score')
    visitor_score = data.get('visitor_score')
    
    if match_id is None or local_score is None or visitor_score is None:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Partido no encontrado'}), 404
    
    if match.is_played:
        return jsonify({'error': 'El partido ya se jugó'}), 400
    
    # Upsert prediction
    pred = Prediction.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    
    if pred:
        pred.local_score = local_score
        pred.visitor_score = visitor_score
        # Recalculate points if match is already played
        if match.is_played:
            pred.puntos = calculate_points(local_score, visitor_score, match.local_score, match.visitor_score)
    else:
        pred = Prediction(
            user_id=current_user.id,
            match_id=match_id,
            local_score=local_score,
            visitor_score=visitor_score,
            puntos=0
        )
        db.session.add(pred)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'prediction': {
            'local_score': pred.local_score,
            'visitor_score': pred.visitor_score,
            'puntos': pred.puntos
        }
    })

@app.route('/api/predictions/<int:match_id>', methods=['DELETE'])
@login_required
def delete_prediction(match_id):
    pred = Prediction.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    if pred:
        db.session.delete(pred)
        db.session.commit()
    return jsonify({'success': True})

# ==========================================
# API - Admin: Update match results
# ==========================================

@app.route('/api/admin/matches/<int:match_id>/result', methods=['POST'])
@login_required
def update_result(match_id):
    if not current_user.is_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    local_score = data.get('local_score')
    visitor_score = data.get('visitor_score')
    
    if local_score is None or visitor_score is None:
        return jsonify({'error': 'Faltan datos'}), 400
    
    match = Match.query.get_or_404(match_id)
    match.local_score = local_score
    match.visitor_score = visitor_score
    match.is_played = True
    db.session.commit()
    
    # Recalculate all predictions for this match
    recalculate_all_points()
    
    return jsonify({'success': True, 'message': 'Resultado actualizado'})

# ==========================================
# API - Ranking
# ==========================================

@app.route('/api/ranking')
def api_ranking():
    users = User.query.all()
    ranking = []
    
    for user in users:
        total = 0
        predictions_count = 0
        correct_exact = 0
        for pred in user.predictions:
            if pred.match.is_played:
                total += pred.puntos
                predictions_count += 1
                if pred.puntos == 7:
                    correct_exact += 1
        
        ranking.append({
            'id': user.id,
            'name': user.name,
            'photo': user.photo,
            'email': user.email,
            'total_points': total,
            'predictions_count': predictions_count,
            'correct_exact': correct_exact,
            'is_admin': user.is_admin
        })
    
    # Sort by total points descending
    ranking.sort(key=lambda x: x['total_points'], reverse=True)
    
    # Add position
    for i, r in enumerate(ranking):
        r['position'] = i + 1
    
    return jsonify(ranking)

# ==========================================
# API - Current User
# ==========================================

@app.route('/api/me')
@login_required
def api_me():
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'photo': current_user.photo,
        'is_admin': current_user.is_admin
    })

# ==========================================
# API - Groups summary
# ==========================================

@app.route('/api/groups')
def api_groups():
    groups = {}
    matches = Match.query.all()
    
    for m in matches:
        group = m.group_name
        if group not in groups:
            groups[group] = {}
        
        for team_name, flag in [(m.local_team, m.local_flag), (m.visitor_team, m.visitor_flag)]:
            if team_name not in groups[group]:
                groups[group][team_name] = {
                    'name': team_name,
                    'flag': flag,
                    'pj': 0, 'pg': 0, 'pe': 0, 'pp': 0,
                    'gf': 0, 'gc': 0, 'pts': 0
                }
            
            if m.is_played:
                stats = groups[group][team_name]
                stats['pj'] += 1
                
                if team_name == m.local_team:
                    stats['gf'] += m.local_score
                    stats['gc'] += m.visitor_score
                    if m.local_score > m.visitor_score:
                        stats['pg'] += 1
                        stats['pts'] += 3
                    elif m.local_score == m.visitor_score:
                        stats['pe'] += 1
                        stats['pts'] += 1
                    else:
                        stats['pp'] += 1
                else:
                    stats['gf'] += m.visitor_score
                    stats['gc'] += m.local_score
                    if m.visitor_score > m.local_score:
                        stats['pg'] += 1
                        stats['pts'] += 3
                    elif m.visitor_score == m.local_score:
                        stats['pe'] += 1
                        stats['pts'] += 1
                    else:
                        stats['pp'] += 1
    
    # Convert to sorted lists
    result = {}
    for group_name, teams in groups.items():
        team_list = list(teams.values())
        team_list.sort(key=lambda x: (x['pts'], x['gf'] - x['gc'], x['gf']), reverse=True)
        result[group_name] = team_list
    
    return jsonify(result)

# ==========================================
# START APP
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_matches()
    app.run(debug=True, port=5000)