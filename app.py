from flask import Flask, render_template, request
import spacy
from dateparser.search import search_dates
import requests

app = Flask(__name__)


nlp = spacy.load("en_core_web_md")

def enhance_city_recognition(text):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": text,
        "format": "json",
        "addressdetails": 1
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        cities = []
        for item in data:
            if 'city' in item['address']:
                cities.append(item['address']['city'])
            elif 'town' in item['address']:
                cities.append(item['address']['town'])
            elif 'village' in item['address']:
                cities.append(item['address']['village'])
        return cities
    else:
        return []

def perform_ner(sentence):
    doc = nlp(sentence)
    entities = {'From': None, 'To': None, 'Date': None, 'Time': None}

    for ent in doc.ents:
        if ent.label_ == 'GPE':
            if not entities['From']:
                entities['From'] = ent.text
            elif not entities['To']:
                entities['To'] = ent.text
        elif ent.label_ == 'DATE':
            parsed_dates = search_dates(ent.text)
            if parsed_dates:
                entities['Date'] = parsed_dates[0][1].strftime('%Y-%m-%d')
        elif ent.label_ == 'TIME':
            entities['Time'] = ent.text

    if not entities['To'] and entities['From']:
        # Enhance recognition for the destination city
        enhanced_cities = enhance_city_recognition(entities['From'])
        if enhanced_cities:
            entities['To'] = enhanced_cities[0]

    return entities

def perform_task_classification(sentence):
    if 'trip' in sentence.lower():
        return 'z1_tripplan'
    elif 'dashboard' in sentence.lower():
        return 'z2_dashboard'
    elif 'settings' in sentence.lower():
        return 'Z3_settings'
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_sentence = request.form['input_sentence']

        ner_output = perform_ner(input_sentence)

        task_class = perform_task_classification(input_sentence)

        output_result = {**ner_output, 'Task_Class': task_class}

        return render_template("index.html", output_result=output_result)

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
