import json
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///analysis_db.db"

class Base(DeclarativeBase):
    pass

class Globalni_Unos_Secera(Base):
    __tablename__ = "globalni_unos_secera"

    godina: Mapped[int] = mapped_column(Integer, primary_key=True)
    kolicina_secera: Mapped[float] = mapped_column(Float, nullable=True)

    def __repr__(self):
        return f"{self.godina} - {self.kolicina_secera}"

class Diabetes_secer_drzava(Base):
    __tablename__ = "diabetes_secer_drzava"

    drzava: Mapped[str] = mapped_column(String(100), primary_key=True)
    postotak: Mapped[float] = mapped_column(Float, nullable=True)
    kolicina: Mapped[float] = mapped_column(Float, nullable=True)

    def __repr__(self):
        return f"{self.godina} - {self.kolicina_secera}"

class Uvoz_Secera_Drzava(Base):
    __tablename__ = "uvoz_secera_drzava"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    godina: Mapped[int] = mapped_column(Integer, nullable=True)
    kolicina_secera: Mapped[float] = mapped_column(Float, nullable=True)
    drzava: Mapped[str] = mapped_column(String(150), nullable=True)

class Pretilost_Podaci(Base):
    __tablename__ = "pretilost_podaci"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    godina: Mapped[int] = mapped_column(Integer, nullable=True)
    drzava: Mapped[str] = mapped_column(String(150), nullable=True)
    postotak: Mapped[float] = mapped_column(Float, nullable=True)


db = SQLAlchemy(model_class=Base)
db.init_app(app)

with app.app_context():
    db.create_all()
    db.session.commit()

@app.route('/')
def home():
    data = db.session.execute(db.select(Globalni_Unos_Secera)).scalars().all()

    godine = [row.godina for row in data]
    kolicina_secera = [row.kolicina_secera for row in data]

    plt.figure(figsize=(10, 5))
    plt.plot(godine, kolicina_secera, marker='o', linestyle='-', color='b', label="Količina šećera")
    plt.title("Prosječna količina šećera kroz godine")
    plt.xlabel("Godina")
    plt.ylabel("Prosječna količina šećera u tonama")
    plt.legend()
    plt.grid()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("home.html", graph_url=graph_url, table_data=data)

@app.route('/postotak_dijabetesa')
def postotak_dijabetesa():
    data = db.session.execute(db.select(Diabetes_secer_drzava)).scalars().all()

    drzave = [row.drzava for row in data]
    postotci = [row.postotak for row in data]
    kolicine = [row.kolicina for row in data]

    plt.figure(figsize=(12, 6))

    bar_width = 0.35
    bar_positions = range(len(drzave))

    plt.bar([p - bar_width / 2 for p in bar_positions], kolicine, bar_width, label="Količina šećera", color='b')

    plt.plot(bar_positions, postotci, color='r', marker='o', label="Postotak dijabetesa", linestyle='-', linewidth=2)

    for i, postotak in enumerate(postotci):
        plt.text(i, postotak + 0.2, f'{postotak:.2f}%', ha='center', va='bottom', color='black', fontweight='bold')

    plt.title("Količina šećera i postotak dijabetesa po državama")
    plt.xlabel("Države")
    plt.ylabel("Vrijednosti")
    plt.xticks(bar_positions, drzave, rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("postotak_dijabetesa.html", graph_url=graph_url, table_data=data)

@app.route('/api/postotak_dijabetesa', methods=['GET'])
def api_postotak_dijabetesa():
    data = db.session.execute(db.select(Diabetes_secer_drzava)).scalars().all()

    result = [
        {
            "drzava": row.drzava,
            "postotak_dijabetesa": row.postotak,
            "kolicina_secera": row.kolicina
        }
        for row in data
    ]

    return jsonify(result)


@app.route('/analiza_pretilosti/<drzava>')
def prikaz_pretilosti(drzava):

    uvoz_data = db.session.execute(db.select(Uvoz_Secera_Drzava)).scalars().all()
    pretilost_data = db.session.execute(db.select(Pretilost_Podaci)).scalars().all()

    uvoz_df = pd.DataFrame([{
        'Drzava': row.drzava,
        'Godina': row.godina,
        'Kolicina_secera': row.kolicina_secera
    } for row in uvoz_data])

    pretilost_df = pd.DataFrame([{
        'Drzava': row.drzava,
        'Godina': row.godina,
        'Postotak_Pretilosti': row.postotak
    } for row in pretilost_data])

    drzava_mapping = {
        "United States": "United States of America",
        "Mexico": "Mexico",
        "India": "India",
        "Indonesia": "Indonesia"
    }

    if drzava not in drzava_mapping:
        return "Odabrana država nije podržana.", 400

    uvoz_df = uvoz_df[uvoz_df['Drzava'] == drzava_mapping[drzava]]
    pretilost_df = pretilost_df[pretilost_df['Drzava'] == drzava]

    combined_df = pd.merge(uvoz_df, pretilost_df, on='Godina', how='inner')
    combined_df = combined_df.sort_values(by='Godina')

    if combined_df.empty:
        return f"Nema podataka za državu {drzava}."

    combined_df = combined_df.drop_duplicates(subset=['Godina'])

    table_data = combined_df.to_dict(orient='records')

    godine = combined_df['Godina']
    kolicina_secera = combined_df['Kolicina_secera']
    postotak_pretilosti = combined_df['Postotak_Pretilosti']

    max_y_value = max(kolicina_secera.max() + 5000, kolicina_secera.max() * 1.2)

    plt.figure(figsize=(14, 8))
    plt.plot(godine, kolicina_secera, marker='o', linestyle='-', color='blue', label=f"Uvoz šećera - {drzava}", linewidth=2)
    plt.title(f"Uvoz šećera i pretilost - {drzava}", fontsize=20)
    plt.xlabel("Godina", fontsize=16)
    plt.ylabel("Količina šećera (t)", fontsize=16)
    plt.xticks(range(1980, 2016, 5), fontsize=12)
    plt.yticks(range(0, int(max_y_value) + 1, 5000), fontsize=12)
    plt.ylim(0, max_y_value)
    plt.xlim(1980, 2015)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    for x, y, pct in zip(godine, kolicina_secera, postotak_pretilosti):
        plt.text(x, y, f"{pct:.1f}%", fontsize=10, ha='center', va='bottom', color='red')

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("analiza_pretilosti.html", graph_url=graph_url, table_data=table_data, drzava=drzava)


@app.route('/api_prikaz_pretilosti/<drzava>', methods=['GET'])
def api_prikaz_pretilosti(drzava):

    uvoz_data = db.session.execute(db.select(Uvoz_Secera_Drzava)).scalars().all()
    pretilost_data = db.session.execute(db.select(Pretilost_Podaci)).scalars().all()

    uvoz_df = pd.DataFrame([{
        'Drzava': row.drzava,
        'Godina': row.godina,
        'Kolicina_secera': row.kolicina_secera
    } for row in uvoz_data])

    pretilost_df = pd.DataFrame([{
        'Drzava': row.drzava,
        'Godina': row.godina,
        'Postotak_Pretilosti': row.postotak
    } for row in pretilost_data])

    drzava_mapping = {
        "United States": "United States of America",
        "Mexico": "Mexico",
        "India": "India",
        "Indonesia": "Indonesia"
    }

    if drzava not in drzava_mapping:
        return jsonify({"error": "Odabrana država nije podržana."}), 400

    uvoz_df = uvoz_df[uvoz_df['Drzava'] == drzava_mapping[drzava]]
    pretilost_df = pretilost_df[pretilost_df['Drzava'] == drzava]

    combined_df = pd.merge(uvoz_df, pretilost_df, on='Godina', how='inner')
    combined_df = combined_df.sort_values(by='Godina')

    if combined_df.empty:
        return jsonify({"error": f"Nema podataka za državu {drzava}."}), 404

    combined_df = combined_df.drop_duplicates(subset=['Godina'])

    return jsonify(combined_df.to_dict(orient='records'))

if __name__ == "__main__":
    app.run(debug=True)



