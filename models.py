from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(300), default='')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    
    def get_total_points(self):
        total = 0
        for pred in self.predictions:
            total += pred.puntos
        return total


class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    local_team = db.Column(db.String(100), nullable=False)
    visitor_team = db.Column(db.String(100), nullable=False)
    local_flag = db.Column(db.String(10), default='🌍')
    visitor_flag = db.Column(db.String(10), default='🌍')
    group_name = db.Column(db.String(10), nullable=False)
    match_date = db.Column(db.String(20), nullable=False)
    match_time = db.Column(db.String(10), nullable=False)
    stadium = db.Column(db.String(100), default='')
    local_score = db.Column(db.Integer, nullable=True)
    visitor_score = db.Column(db.Integer, nullable=True)
    is_played = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    predictions = db.relationship('Prediction', backref='match', lazy=True)


class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    local_score = db.Column(db.Integer, nullable=False)
    visitor_score = db.Column(db.Integer, nullable=False)
    puntos = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'match_id', name='unique_prediction'),)