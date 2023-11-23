import mysql.connector
from jinja2 import Template

# MySQL database connection configuration
db_config = {
    'host': '127.0.0.1',
    'user': 'loser',
    'password': 'dupa',
    'database': 'wyniki'
}

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
    partia = row[6]
    
    if date not in data:
        data[date] = {}
    
    if nrGlos not in data[date]:
        data[date][nrGlos] = {
            'godz': row[4],
            'temat': row[5],
            'partie': {}
        }
    
    if partia not in data[date][nrGlos]['partie']:
        data[date][nrGlos]['partie'][partia] = {
            'czlonkowie': row[7],
            'za': row[8],
            'przeciw': row[9],
            'wstrzymal': row[10],
            'nieobecni': row[11]
        }





# Jinja2 template for HTML generation
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Sejm Data</title>
    <link rel="stylesheet" type="text/css" href="styles.css">
</head>
<body>
    {% for date, glosy in data.items()|reverse %}
        <h2>{{ date }}</h2>
        <table border="1">
            <tr>
                <th>NR GLOS.</th>
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
                    <td>{{ nrGlos }}</td>
                    <td>{{ info.godz }}</td>
                    <td>{{ info.temat }}</td>
                    {% for partie, votes in info.partie.items() %}
                        <td style="background-color: rgb(
                            {{ ((200 * votes.przeciw + 66 * (votes.nieobecni + votes.wstrzymal)) // votes.czlonkowie) + 50}},
                            {{ ((200 * votes.za + (66 * (votes.wstrzymal + votes.nieobecni))) // votes.czlonkowie) + 50}},
                            {{ (122 * (votes.wstrzymal + votes.nieobecni) // votes.czlonkowie) + 50}}
                        );">
                            <h3>{{ partie }} ({{ votes.czlonkowie }})</h3>
                            <p>{{ votes.za }} / {{ votes.przeciw }} / {{ votes.wstrzymal }} / {{ votes.nieobecni }}</p>
                        </td>
                    {% endfor %}
                </tr>
            {% endfor %}
        </table>
    {% endfor %}
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
