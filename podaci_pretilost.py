import pandas as pd
import requests
import sqlite3

def get_world_bank_data(indicator, country_code, start_year, end_year):
    base_url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 1000
    }

    response = requests.get(base_url, params=params)
    print(f"Statusni kod odgovora: {response.status_code}")

    if response.status_code == 200:
        try:
            json_response = response.json()

            if len(json_response) > 1 and json_response[1] is not None:
                data = json_response[1]

                return pd.DataFrame(data)

            else:
                print("Nema podataka za zadane parametre ili struktura odgovora nije očekivana.")
                return pd.DataFrame()
        except Exception as e:
            print(f"Greška prilikom parsiranja JSON odgovora: {e}")
            print("Neparsiran odgovor:", response.text)
            return pd.DataFrame()
    else:
        print(f"Greška u dohvaćanju podataka: Statusni kod {response.status_code}")
        print("Tekst odgovora:", response.text)
        return pd.DataFrame()

obesity_data = get_world_bank_data("SH.STA.OWGH.ZS", "MEX", 1980, 2014)
obesity_data = obesity_data[obesity_data['value'].notna()]

print(obesity_data.columns)

for index, row in obesity_data.iterrows():
    print(f"{row['date']} - {row['country']['value']} - {row['value']}")


db = sqlite3.connect("instance/analysis_db.db")
cursor = db.cursor()

for _, row in obesity_data.iterrows():
    cursor.execute("""
        INSERT OR REPLACE INTO pretilost_podaci (godina, drzava, postotak)
        VALUES (?, ?, ?)
    """, (int(row['date']), row['country']['value'], float(row['value'])))

db.commit()
db.close()

print("Podaci su uspješno pohranjeni u tablicu 'pretilost_podaci'.")

