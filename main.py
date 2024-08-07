from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_socketio import SocketIO
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
import openai
import itertools
import os
import secrets

# Charger les variables d'environnement
load_dotenv()

# Initialiser Flask et extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)  # Génération d'une clé secrète aléatoire pour plus de sécurité
socketio = SocketIO(app)

# Ajouter des en-têtes de sécurité
@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self';"
    return response

# Charger les clés API OpenAI
api_keys = [
    os.getenv('OPENAI_API_KEY_1'),
    os.getenv('OPENAI_API_KEY_2'),
    os.getenv('OPENAI_API_KEY_3')
]

# Créer un itérateur cyclique pour les clés API
api_key_cycle = itertools.cycle(api_keys)

# Fonction pour lire les URL des projets depuis le fichier
def load_projects():
    with open('repourls.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

# Charger la liste des projets
projects = load_projects()

# Formulaire de recherche
class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        query = form.search_query.data
        result = search_projects(query)
        return render_template('index.html', form=form, result=result)
    return render_template('index.html', form=form, result=None)

def search_projects(query, max_projects=20):
    # Filtrer les projets basés sur les mots-clés avant d'envoyer la requête à GPT-4
    filtered_projects = [project for project in projects if query.lower() in project.lower()]

    # Limiter le nombre de projets pour réduire la taille du prompt
    limited_projects = filtered_projects[:max_projects] if filtered_projects else projects[:max_projects]

    # Construire le prompt avec une introduction claire
    prompt = (
        f"You are an assistant that helps to find GitHub projects from the following list based on the search query '{query}':\n"
        f"{limited_projects}\n"
        "List the URLs of the projects that match the search query."
    )

    # Sélectionner la clé API suivante
    current_api_key = next(api_key_cycle)
    openai.api_key = current_api_key

    # Utiliser l'API OpenAI pour rechercher des projets
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that helps to find GitHub projects."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )

    # Extraire les URLs des projets de la réponse
    result = response.choices[0].message['content'].strip()
    return result

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))