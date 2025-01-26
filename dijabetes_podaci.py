import pandas as pd
import requests
import sqlite3

food_data = pd.read_csv("static/files/food_data.csv", encoding='latin1')
food_data.columns = food_data.columns.str.replace('Y', '', regex=False)

vrsta_secera = [
    "Sugar cane", "Sugar beet", "Sugar (Raw Equivalent)", "Sweeteners", "Other", "Sugar Crops", "Sugar & Sweeteners"
]
filtered_data = food_data[food_data['Item'].isin(vrsta_secera)]
data_2011 = filtered_data[['Area', 'Item', '2011']]
result_2011 = data_2011.groupby('Area')['2011'].sum().reset_index()
result_2011.columns = ['Država', 'Količina šećera']


def get_world_bank_data(indicator, start_year, end_year):
    base_url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 1000
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()[1]
        return pd.DataFrame(data)
    else:
        print(f"Greška u dohvaćanju podataka: {response.status_code}")
        return pd.DataFrame()

diabetes_data = get_world_bank_data("SH.STA.DIAB.ZS", 1990, 2021)

if not diabetes_data.empty:
    diabetes_data_2011 = diabetes_data[diabetes_data['date'] == '2011']

    result = []

    for _, row in diabetes_data_2011.iterrows():
        country_data = row['country']
        percentage = row['value']

        if isinstance(country_data, dict):
            country_name = country_data.get('value')
        else:
            country_name = None

        if country_name and pd.notna(percentage) and percentage != 0:
            result.append({'Država': country_name, 'Postotak': percentage})

    diabetes_df = pd.DataFrame(result)

    continents_to_countries = {
        "Middle East & North Africa": "Egypt",
        "Europe & Central Asia": "Germany",
        "Latin America & Caribbean (excluding high income)": "United States of America",
        "Latin America & Caribbean": "Brazil",
        "Africa Western and Central": "Nigeria",
    }

    final_result = []

    for continent, country in continents_to_countries.items():
        diabetes_row = diabetes_df[diabetes_df['Država'] == continent]
        if not diabetes_row.empty:
            diabetes_percentage = diabetes_row.iloc[0]['Postotak']
        else:
            diabetes_percentage = None

        sugar_row = result_2011[result_2011['Država'] == country]
        if not sugar_row.empty:
            sugar_quantity = sugar_row.iloc[0]['Količina šećera']
        else:
            sugar_quantity = None

        final_result.append({
            'Država': country,
            'Postotak dijabetesa': diabetes_percentage,
            'Količina uvezenog šećera': sugar_quantity
        })

    final_df = pd.DataFrame(final_result)
    print(final_df)

else:
    print("Nema dostupnih podataka za traženi indikator.")

db = sqlite3.connect("instance/analysis_db.db")
cursor = db.cursor()

for _, row in final_df.iterrows():
    cursor.execute(f"""
        INSERT OR REPLACE INTO diabetes_secer_drzava
        VALUES ('{row['Država']}', {round(row['Postotak dijabetesa'], 2)}, {row['Količina uvezenog šećera']})
    """)

db.commit()
db.close()

print("Podaci su uspjesno pohranjeni u bazu")



