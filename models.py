from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    alert_email = db.Column(db.String(150), nullable=True)
    domains = db.relationship('Domain', backref='owner', lazy=True)


# Domain Model
class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    last_scanned = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="unknown")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scan_history = db.relationship('ScanHistory', backref='domain', lazy=True)


# Scan History Model
class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    permutations_checked = db.Column(db.Integer, nullable=True)
    existing_domains = db.Column(db.Integer, nullable=True)
    domains_alerted = db.Column(db.Text, nullable=True)  # JSON string
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)


# Scan Settings Model
class ScanSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    custom_cron = db.Column(db.String(100), nullable=True)


class ScanDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scan_history.id'), nullable=False)
    domain_name = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    whois_name_servers = db.Column(db.String(255), nullable=True)
    whois_registrar = db.Column(db.String(255), nullable=True)
    whois_country = db.Column(db.String(50), nullable=True)
    whois_creation_date = db.Column(db.String(50), nullable=True)
    whois_emails = db.Column(db.String(255), nullable=True)
    similarity_score = db.Column(db.Integer, nullable=True)
    reputation = db.Column(db.String(50), nullable=True)


class Whitelist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    whitelisted_domain = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    domain = db.relationship('Domain', backref=db.backref('whitelist', lazy=True))

    def __repr__(self):
        return f"<Whitelist {self.whitelisted_domain} for Domain {self.domain_id}>"
