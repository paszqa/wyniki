import os
import requests
from bs4 import BeautifulSoup
import mysql.connector
from urllib.parse import urljoin
from datetime import datetime, timedelta
import configparser


def read_last_conf(file_path):
    """Reads the last sitting and voting IDs from the config file."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                return int(lines[0].strip()), int(lines[1].strip())
    except FileNotFoundError:
        print(f"{file_path} not found. Starting from default values.")
    except ValueError:
        print("Invalid values in config file. Starting from default values.")
    return 1, 1  # Default values if file is missing or corrupted

def write_last_conf(file_path, sitting_id, voting_id):
    """Writes the last sitting and voting IDs to the config file."""
    with open(file_path, 'w') as file:
        file.write(f"{sitting_id}\n{voting_id}\n")

def check_api_for_data(sitting_id, voting_id):
    """Checks if data exists for the given sitting and voting IDs."""
    url = f"https://api.sejm.gov.pl/sejm/term10/votings/{sitting_id}/{voting_id}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error checking API: {e}")
        return False

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
    print(response.text)
    return response.text

def extract_title_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title_content = soup.find('div', id='title_content')

    if title_content:
        h1_text = title_content.find('h1').get_text(strip=True)
        elements = h1_text.split()

        if len(elements) >= 9:
            print("Found "+str(len(elements))+" elements. Continuing")
            nrPos = elements[6].replace('.', '')
            raw_date = elements[3]

            # Parse the date from DD-MM-YYYY to YYYY-MM-DD format
            date_object = datetime.strptime(raw_date, '%d-%m-%Y')
            formatted_date = date_object.strftime('%Y-%m-%d')
            current_date = datetime.now()
            compare_date = datetime.now() - timedelta(hours=24)
            if date_object < compare_date:
                print("Date is in the past: "+str(date_object)+" today: "+str(compare_date)+". Continuing")
                return nrPos, formatted_date
            else:
                print("Date is not in the past. Exiting...")
                exit()
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

def save_to_database(nrGlos, glosLink, date, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, godz, db_config):
    connection = None

    try:
        # Replace "-" with 0 for numeric fields
        za = int(za) if za != "-" else 0
        przeciw = int(przeciw) if przeciw != "-" else 0
        wstrzymal = int(wstrzymal) if wstrzymal != "-" else 0
        nieobecni = int(nieobecni) if nieobecni != "-" else 0

        connection = mysql.connector.connect(**db_config)
 
        cursor = connection.cursor()
        print("Adding with date: "+date)
        cursor.execute('''
            INSERT INTO sejm (nrGlos, glosLink, godz, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (nrGlos, glosLink, godz, temat, partia, czlonkowie, za, przeciw, wstrzymal, nieobecni, nrPos, date))

        connection.commit()
        print('Data saved to the database successfully.')

    except Exception as e:
        print("Error:", e)

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    config_file = "last.conf"
    db_config = load_db_config()

    # Load last processed sitting and voting IDs
    last_sitting_id, last_voting_id = read_last_conf(config_file)

    # Check for data with lastSittingID and lastVotingID + 1
    next_voting_id = last_voting_id + 1
    if check_api_for_data(last_sitting_id, next_voting_id):
        parse_voting_data(last_sitting_id, next_voting_id, db_config)
        write_last_conf(config_file, last_sitting_id, next_voting_id)
        return

    # Check for data with lastSittingID + 1 and votingID set to 1
    next_sitting_id = last_sitting_id + 1
    if check_api_for_data(next_sitting_id, 1):
        parse_voting_data(next_sitting_id, 1, db_config)
        write_last_conf(config_file, next_sitting_id, 1)
        return

    # If no data found, leave last.conf unchanged
    print("No new data found. Config file remains unchanged.")


def parse_voting_data(sitting_id, vote_id, db_config):
    print("Getting data for Sitting ID: "+str(sitting_id)+" and vote ID: "+str(vote_id))
    url = f"https://api.sejm.gov.pl/sejm/term10/votings/{sitting_id}/{vote_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()  # Parse JSON response

        # Extract main object values
        date_raw = data.get("date", "")  # Original date format
        print("Raw date: "+date_raw)
        sitting = data.get("sitting", "")
        title = data.get("title", "")
        topic = data.get("topic", "")
        votes = data.get("votes", [])
        
        date = date_raw.split("T")[0] if "T" in date_raw else date_raw  # Extract date part
        print("Date: "+date)
        time = date_raw.split("T")[1] if "T" in date_raw else "00:00:00"  # Extract time part
        print("Time: "+time)
        # Initialize club counts
        club_data = {}

        for vote in votes:
            club = vote.get("club", "Unknown")
            vote_choice = vote.get("vote", "ABSENT")

            if club not in club_data:
                club_data[club] = {
                    "memberCount": 0,
                    "YES": 0,
                    "NO": 0,
                    "ABSTAIN": 0,
                    "ABSENT": 0
                }

            club_data[club]["memberCount"] += 1
            club_data[club][vote_choice] += 1

        # Call save_to_database for each club
        for club, counts in club_data.items():
            print("date 2: "+date)
            save_to_database(
                vote_id,
                " ",  # Assuming a placeholder for an empty field
                date,
                f"{title} - {topic}",
                club,
                counts["memberCount"],
                counts["YES"],
                counts["NO"],
                counts["ABSTAIN"],
                counts["ABSENT"],
                sitting,
                time,
                db_config
            )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
    except KeyError as e:
        print(f"Missing expected data in API response: {e}")


if __name__ == "__main__":
    main()
    
    
    
