import pandas as pd
import sqlite3


food_data = pd.read_csv("static/files/food_data.csv", encoding='latin1')
#print("Podaci iz Kaggle CSV-a:")
#print(food_data.head())

food_data.columns = food_data.columns.str.replace('Y', '', regex=False)

vrsta_secera = [
    "Sugar cane", "Sugar beet", "Sugar (Raw Equivalent)", "Sweeteners", "Other", "Sugar Crops", "Sugar & Sweeteners"
]

filtered_data = food_data[food_data['Item'].isin(vrsta_secera)]

result = []

for _, row in filtered_data.iterrows():

    years = [str(year) for year in range(1961, 2014)]

    for year in years:

        quantity = row[year]

        result.append({
            "Država": row['Area'],
            "Vrsta_secera": row['Item'],
            "Kolicina_secera_kroz_godinu": quantity,
            "Godina": year
        })

result_df = pd.DataFrame(result)

average_per_year = result_df.groupby('Godina')['Kolicina_secera_kroz_godinu'].mean().reset_index()

average_per_year.rename(columns={'Kolicina_secera_kroz_godinu': 'Prosjecna_kolicina_secera'}, inplace=True)

print(average_per_year)

db = sqlite3.connect("instance/analysis_db.db")
cursor = db.cursor()

for _, row in average_per_year.iterrows():
    cursor.execute(f"""
        INSERT OR REPLACE INTO globalni_unos_secera
        VALUES ({row['Godina']}, {row['Prosjecna_kolicina_secera']})
    """)

db.commit()
db.close()

print("Podaci su uspjesno pohranjeni u bazu")

