import os
import requests
from bs4 import BeautifulSoup
import mysql.connector
from urllib.parse import urljoin
from datetime import datetime
import configparser


def read_current_day(file_path='currentDay.conf'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    else:
        print(f"Error: File '{file_path}' not found.")
        exit()

def write_current_day(current_day, file_path='currentDay.conf'):
    with open(file_path, 'w') as file:
        file.write(current_day)

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

def download_website(url):
    response = requests.get(url)
    return response.text

def extract_title_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title_content = soup.find('div', id='title_content')

    if title_content:
        h1_text = title_content.find('h1').get_text(strip=True)
        elements = h1_text.split()

        if len(elements) >= 8:
            nrPos = elements[6].replace('.', '')
            raw_date = elements[3]

            # Parse the date from DD-MM-YYYY to YYYY-MM-DD format
            date_object = datetime.strptime(raw_date, '%d-%m-%Y')
            formatted_date = date_object.strftime('%Y-%m-%d')

            return nrPos, formatted_date
        else:
            print("Fewer than 8 title elements. Exiting program.")
            exit()
    return None, None

def extract_first_table_rows(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    
    if table:
        tbody = table.find('tbody')
        
        if tbody:
            rows = tbody.find_all('td')
            return rows
        else:
            print('No <tbody> found in the table.')
            return []
    else:
        print('No table found on the website.')
        return []

def extract_second_site_data(link):
    response = requests.get(link)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    table = soup.find('table', class_='kluby')
    
    if table:
        tbody = table.find('tbody', class_='center')
        
        if tbody:
            rows = tbody.find_all('td')
            return rows
        else:
            print('No <tbody> with class "center" found in the second table.')
            return []
    else:
        print('No table with class "kluby" found on the second website.')
        return []

def save_to_database(nrGlos, godz, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, date, db_config):
    connection = None

    try:
        # Replace "-" with 0 for numeric fields
        za = int(za) if za != "-" else 0
        przeciw = int(przeciw) if przeciw != "-" else 0
        wstrzymal = int(wstrzymal) if wstrzymal != "-" else 0
        nieobecni = int(nieobecni) if nieobecni != "-" else 0

        connection = mysql.connector.connect(**db_config)
 
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO sejm (nrGlos, godz, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (nrGlos, godz, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, date))

        connection.commit()
        print('Data saved to the database successfully.')

    except Exception as e:
        print("Error:", e)

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    current_day = read_current_day()
    db_config = load_db_config()

    first_site_url = f'https://www.sejm.gov.pl/Sejm10.nsf/agent.xsp?symbol=listaglos&IdDnia={current_day}'
    first_site_html_content = download_website(first_site_url)
    
    if first_site_html_content:
        # Extract additional information from the title
        nrPos, date = extract_title_info(first_site_html_content)
        
        first_site_rows = extract_first_table_rows(first_site_html_content)

        if first_site_rows:
            for i in range(0, len(first_site_rows), 3):
                nrGlos = first_site_rows[i].get_text(strip=True)
                glosLink = urljoin(first_site_url, first_site_rows[i].find('a')['href'])
                godz = first_site_rows[i + 1].get_text(strip=True)
                temat = first_site_rows[i + 2].get_text(strip=True)
                second_site_rows = extract_second_site_data(glosLink)
                
                for j in range(0, len(second_site_rows), 7):
                    partia = second_site_rows[j].get_text(strip=True)
                    czlonkowie = second_site_rows[j + 1].get_text(strip=True)  # Extract value from 2nd <td>
                    za = second_site_rows[j + 3].get_text(strip=True)
                    przeciw = second_site_rows[j + 4].get_text(strip=True)
                    wstrzymal = second_site_rows[j + 5].get_text(strip=True)
                    nieobecni = second_site_rows[j + 6].get_text(strip=True)
                    
                    save_to_database(nrGlos, godz, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, date, db_config)

            # Increment idDnia and save it back to currentDay.conf
            current_day = str(int(current_day) + 1)
            write_current_day(current_day)
                
        else:
            print('No rows found in the first table.')
    else:
        print('Failed to download the first website.')

if __name__ == "__main__":
    main()
