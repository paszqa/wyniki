import mysql.connector
from jinja2 import Template
import configparser
import datetime

# MySQL database connection configuration
def load_db_config(config_file='db.conf'):
    config = configparser.ConfigParser()
    config.read(config_file)

    db_config = {
        'host': config.get('database', 'host'),
        'user': config.get('database', 'user'),
        'password': config.get('database', 'password'),
        'database': config.get('database', 'database')
    }

    return db_config

db_config = load_db_config()

# Connect to the MySQL database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Query to retrieve data from the "sejm" table
query = "SELECT * FROM sejm ORDER BY date, nrGlos, czlonkowie DESC"
cursor.execute(query)

# Fetch all rows from the result set
rows = cursor.fetchall()

# Close the database connection
cursor.close()
conn.close()

# Organize the data for rendering
data = {}
for row in rows:
    date = row[2].strftime('%Y-%m-%d')  # Format date as needed
    nrGlos = row[3]
    partia = row[7]
    glosLink = row[4]
    print("glosLink: "+glosLink)
    czlonkowie = int(row[8]) if row[8] != "-" else 0
    za = int(row[9]) if row[9] != "-" else 0
    przeciw = int(row[10]) if row[10] != "-" else 0
    wstrzymal = int(row[11]) if row[11] != "-" else 0
    nieobecni = int(row[12]) if row[12] != "-" else 0

    if date not in data:
        data[date] = {}
    
    if nrGlos not in data[date]:
        data[date][nrGlos] = {
            'godz': row[5],
            'temat': row[6],
            'glosLink' : row[4],
            'partie': {}
        }
    
    if partia not in data[date][nrGlos]['partie']:
        data[date][nrGlos]['partie'][partia] = {
            'czlonkowie': row[8],
            'za': row[9],
            'przeciw': row[10],
            'wstrzymal': row[11],
            'nieobecni': row[12]
        }

today = datetime.datetime.now()



# Jinja2 template for HTML generation
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Sejm Data</title>
    <link rel="stylesheet" type="text/css" href="styles.css">
</head>
<body>
    <div class="main">
        <div class="mainleft">
            Wyniki głosowań Sejmu RP
        </div>
        <div class="mainright">
            Ta strona jest nieoficjalna. Zbiera dane z oficjalnej strony Sejmu RP oraz prezentuje je w przystępny i czytelny sposób. Dane są aktualizowane każdego dnia w nocy. Nie odpowiadam za błędne działanie aplikacji lub niepoprawne dane. Ostatnia aktualizacja: {% today %}
        </div>
    </div>
    {% for date, glosy in data.items()|reverse %}
        <h2>{{ date }}</h2>
        <table border="1">
            <tr>
                <th>NR GŁOS.</th>
                <th>GODZ.</th>
                <th>TEMAT</th>
                {% for key, value in glosy.items() %}
                    {% if key == 'partie' %}
                        {% for party, counts in value.items() %}
                            <th>{{ party }}</th>
                        {% endfor %}
                    {% endif %}
                {% endfor %}
            </tr>
            {% for nrGlos, info in glosy.items() %}
                <tr>
                    <td><a href="{{ info.glosLink }}">{{ nrGlos }}</a></td>
                    <td>{{ info.godz }}</td>
                    <td>{{ info.temat }}</td>
                    {% for partie, votes in info.partie.items() %}
                        <td style="background-color: rgb(
                            {{ ((200 * votes.przeciw + 66 * (votes.nieobecni + votes.wstrzymal)) // votes.czlonkowie) + 50}},
                            {{ ((200 * votes.za + (66 * (votes.wstrzymal + votes.nieobecni))) // votes.czlonkowie) + 50}},
                            {{ (122 * (votes.wstrzymal + votes.nieobecni) // votes.czlonkowie) + 50}}
                        );">
                            <div class="divcell">
                            <div class="up">{{ partie }} ({{ votes.czlonkowie }})</div>
                            <div class="down">{{ votes.za }} / {{ votes.przeciw }} / {{ votes.wstrzymal }} / {{ votes.nieobecni }}</div>
                            </div>
                        </td>
                    {% endfor %}
                </tr>
            {% endfor %}
        </table>
    {% endfor %}

<div id="sfcgfrx5pgr8tgdzj1q4cl6gkdt368jhccu"></div>
<script type="text/javascript" src="https://counter8.optistats.ovh/private/counter.js?c=gfrx5pgr8tgdzj1q4cl6gkdt368jhccu&down=async" async></script>
<noscript><a href="https://www.freecounterstat.com" title="hit counter"><img src="https://counter8.optistats.ovh/private/freecounterstat.php?c=gfrx5pgr8tgdzj1q4cl6gkdt368jhccu" border="0" title="hit counter" alt="hit counter"></a></noscript>

    paszqa.github.io - https://github.com/paszqa/ - 2023
</body>
</html>
"""

# Render the HTML using Jinja2 template
template = Template(html_template)
rendered_html = template.render(data=data)

# Save the generated HTML to a file
with open('docs/index.html', 'w') as file:
    file.write(rendered_html)

print("HTML file generated successfully.")
