import pandas as pd
import sqlite3

file_path = 'static/files/food_data.csv'
food_data = pd.read_csv(file_path, encoding='latin1')

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
            "Godina": int(year),
            "Kolicina_secera_kroz_godinu": quantity,
        })

result_df = pd.DataFrame(result)

result_df = result_df.groupby(['Država', 'Godina'], as_index=False).agg({
    'Kolicina_secera_kroz_godinu': 'sum'
})

selected_countries = ['United States of America', 'Mexico', 'India', 'Indonesia']
selected_years = list(range(1988, 2014))

filtered_result_df = result_df[
    (result_df['Država'].isin(selected_countries)) & (result_df['Godina'].isin(selected_years))
]

filtered_result_df.reset_index(drop=True, inplace=True)

print(filtered_result_df)

db = sqlite3.connect("instance/analysis_db.db")
cursor = db.cursor()

for _, row in filtered_result_df.iterrows():
    cursor.execute("""
        INSERT INTO uvoz_secera_drzava (godina, kolicina_secera, drzava)
        VALUES (?, ?, ?)
    """, (int(row['Godina']), float(row['Kolicina_secera_kroz_godinu']), row['Država']))

db.commit()
db.close()

print("Podaci su uspješno pohranjeni u tablicu 'uvoz_secera_drzava'.")



