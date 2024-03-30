from flask import Flask, render_template, request
import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, extract, and_
from collections import defaultdict
import calendar


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:P%40stgre428916@localhost:5432/spot_db'
db = SQLAlchemy(app)

class SpotKite(db.Model):
    __tablename__ = 'kite_spots'
    spot_id = db.Column(db.String, primary_key=True)
    spot = db.Column(db.String)
    lat = db.Column(db.String)
    long = db.Column(db.String)
    pays = db.Column(db.String)

class SpotObservation(db.Model):
    __tablename__ = 'spot_observations'
    obs_id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(50), db.ForeignKey('kite_spots.spot_id'), nullable=False)
    date_obs = db.Column(db.Date, nullable=False)
    heure = db.Column(db.Integer, nullable=False)
    vitesse_vent = db.Column(db.Numeric, nullable=True)
    direction_vent = db.Column(db.Numeric, nullable=True)

class DailyMaxWindSpeed(db.Model):
    __tablename__ = 'daily_max_wind_speed'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('spot.id'))  # Assurez-vous que cette définition correspond à votre modèle
    date_obs = db.Column(db.Date, nullable=False)
    max_wind_speed = db.Column(db.Numeric)

class WindSpeedSummary(db.Model):
    __tablename__ = 'monthly_wind_speed_summary_2'
    spot_id = db.Column(db.String, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    pct_12_16 = db.Column(db.Float)
    pct_17_21 = db.Column(db.Float)
    pct_22_27 = db.Column(db.Float)
    pct_28_33 = db.Column(db.Float)
    pct_34_40 = db.Column(db.Float)
    pct_41_90 = db.Column(db.Float)

@app.route('/template')
def list_spots():
    spots = SpotKite.query.all()
    return render_template('template.html', spots=spots)


@app.route('/spot/<string:spot_id>', methods=['GET', 'POST'])
def spot_details(spot_id):
    spot = SpotKite.query.filter_by(spot_id=spot_id).first_or_404()

    direction_distribution_raw = db.session.query(
        SpotObservation.direction_vent % 360,
        func.count().label('direction_count')
    ).filter(
        SpotObservation.spot_id == spot_id,
        SpotObservation.direction_vent.isnot(None)
    ).group_by(SpotObservation.direction_vent % 360
               ).order_by(SpotObservation.direction_vent % 360
                          ).all()

    # À ce stade, direction_distribution_raw contient des paires (direction ajustée, count)
    # Triées par direction du vent ajustée

    # Trouver l'index pour la valeur 180 degrés et réorganiser
    start_index = next((i for i, pair in enumerate(direction_distribution_raw) if pair[0] >= 180), None)
    if start_index is not None:
        direction_distribution_reordered = direction_distribution_raw[start_index:] + direction_distribution_raw[
                                                                                      :start_index]
    else:
        direction_distribution_reordered = direction_distribution_raw

    direction_labels = [str(pair[0]) for pair in direction_distribution_reordered]
    direction_data = [pair[1] for pair in direction_distribution_reordered]
    colors = ['rgba(255, 0, 0, 0.6)' if value > 25 else 'rgba(0, 0, 255, 0.6)' for value in direction_data]

    # Récupérer et formater les données pour Chart.js
    query_results = WindSpeedSummary.query.filter_by(spot_id=spot_id).all()

    # Transformer les résultats de la requête en dictionnaires
    data_list = []
    for entry in query_results:
        entry_dict = {
            'month': entry.month,
            'pct_12_16': entry.pct_12_16,
            'pct_17_21': entry.pct_17_21,
            'pct_22_27': entry.pct_22_27,
            'pct_28_33': entry.pct_28_33,
            'pct_34_40': entry.pct_34_40,
            'pct_41_90': entry.pct_41_90,
            # Continuez pour les autres champs
        }
        data_list.append(entry_dict)

    # Préparation des données pour le graphique
    response_data = {
        'labels': ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        'datasets': [
            {'label': '12-16 knots', 'data': [d['pct_12_16'] for d in data_list],
             'backgroundColor': 'rgba(255, 99, 132, 0.5)'},
            {'label': '17-21 knots', 'data': [d['pct_17_21'] for d in data_list],
             'backgroundColor': 'rgba(0, 99, 132, 0.5)'},
            {'label': '22-27 knots', 'data': [d['pct_22_27'] for d in data_list],
             'backgroundColor': 'rgba(140, 99, 132, 0.5)'},
            {'label': '28-33 knots', 'data': [d['pct_28_33'] for d in data_list],
             'backgroundColor': 'rgba(190, 99, 132, 0.5)'},
            {'label': '34-40 knots', 'data': [d['pct_34_40'] for d in data_list],
             'backgroundColor': 'rgba(255, 80, 132, 0.5)'},
            {'label': '41-90 knots', 'data': [d['pct_41_90'] for d in data_list],
             'backgroundColor': 'rgba(200, 99, 255, 0.5)'},
            # Répétez pour les autres plages de vitesse
        ]
    }
    recommendation = None
    if request.method == 'POST':
        # Récupération des données du formulaire
        month_of_departure = request.form.get('month_of_departure')
        kite_sizes = {
            '12-16 knots': request.form.get('kite_size_12_16'),
            '17-21 knots': request.form.get('kite_size_17_21'),
            '22-27 knots': request.form.get('kite_size_22_27'),
            '28-33 knots': request.form.get('kite_size_28_33'),
            '34-40 knots': request.form.get('kite_size_34_40'),
        }

        # Trouver la plage de vent correspondante au pourcentage maximal pour le mois de départ
        max_percentage = 0
        max_percentage_label = None
        for dataset in response_data['datasets']:
            if dataset['data'][int(month_of_departure) - 1] > max_percentage:
                max_percentage = dataset['data'][int(month_of_departure) - 1]
                max_percentage_label = dataset['label']

        # Déterminer la taille d'aile recommandée
        recommended_kite_size = kite_sizes.get(max_percentage_label)
        recommendation = f"Sur ce spot, je te recommande de prendre ta {recommended_kite_size}m"

    return render_template('spot_details.html', spot=spot, spot_id=spot_id,
                           direction_labels=direction_labels, direction_data=direction_data, colors=colors,
                           data=response_data, recommendation=recommendation)

if __name__ == '__main__':
    app.run(debug=True)