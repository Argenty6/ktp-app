from flask import Flask
import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:P%40stgre428916@localhost:5432/spot_db'
db = SQLAlchemy(app)

class SpotKite(db.Model):
    __tablename__ = 'kite_spots'
    spot_id = db.Column(db.String, primary_key=True)
    spot = db.Column(db.String)
    lat = db.Column(db.String)
    long= db.column(db.String)
    pays = db.Column(db.String)

with app.app_context():
    spot = SpotKite.query.first()
    if spot:
        print("Données récupérées :", spot.spot)
    else:
        print("Aucune donnée trouvée.")