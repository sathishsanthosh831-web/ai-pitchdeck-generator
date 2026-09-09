from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    decks = db.relationship('PitchDeck', backref='user', lazy=True)

class PitchDeck(db.Model):
    __tablename__ = 'pitch_decks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(80), nullable=True)
    tagline = db.Column(db.String(250), nullable=True)
    theme = db.Column(db.String(50), default='midnight')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    slides = db.relationship('Slide', backref='deck', lazy=True, cascade="all, delete-orphan")

class Slide(db.Model):
    __tablename__ = 'slides'
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('pitch_decks.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(250), nullable=True)
    bullets_json = db.Column(db.Text, nullable=True)
    metrics_json = db.Column(db.Text, nullable=True)
    speaker_notes = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0)
