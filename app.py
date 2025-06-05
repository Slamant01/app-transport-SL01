
import streamlit as st
import pandas as pd
import openrouteservice
from openrouteservice import convert
import time

st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")

# Clé API OpenRouteService
import os
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

def get_distance_duration(dep, arr):
    try:
        coords = client.pelias_search(text=dep)['features'][0]['geometry']['coordinates']
        coord_dep = coords[::-1]  # (lat, lon)
        coords = client.pelias_search(text=arr)['features'][0]['geometry']['coordinates']
        coord_arr = coords[::-1]
        route = client.directions((coord_dep, coord_arr), profile='driving-hgv', format='geojson')
        distance_km = route['features'][0]['properties']['segments'][0]['distance'] / 1000
        duration_h = route['features'][0]['properties']['segments'][0]['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2)
    except:
        return None, None


def calcul_cout_transport(distance_km, duree_heure, nb_palettes):
    if distance_km is None or duree_heure is None:
        return None, None
    CK = 0.60  # €/km
    CC = 28.96  # €/h
    CJ = 260.35  # €/jour
    CG = 3.05   # €/h
    cout_total = distance_km * CK + duree_heure * CC + CJ + duree_heure * CG
    cout_palette = cout_total / nb_palettes if nb_palettes > 0 else None
    return round(cout_total, 2), round(cout_palette, 2)

st.title("🚚 Estimation des coûts de transport (Frigo LD_EA)")

uploaded_file = st.file_uploader("📁 Importer un fichier CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("📋 Données importées :", df)

    resultats = []
    with st.spinner("🔄 Calcul en cours..."):
        for index, row in df.iterrows():
            dep = row['Adresse_Depart']
            arr = row['Adresse_Arrivee']
            nb_palettes = row['Nb_Palettes']
            dist, duree = get_distance_duration(dep, arr)
            cout_total, cout_par_palette = calcul_cout_transport(dist, duree, nb_palettes)
            resultats.append({
                "Adresse_Depart": dep,
                "Adresse_Arrivee": arr,
                "Distance_km": dist,
                "Duree_h": duree,
                "Nb_Palettes": nb_palettes,
                "Cout_Total (€)": cout_total,
                "Cout_par_Palette (€)": cout_par_palette
            })
            time.sleep(1.1)  # éviter dépassement de quota API gratuit

    df_result = pd.DataFrame(resultats)
    st.success("✅ Calculs terminés")
    st.dataframe(df_result)

    csv = df_result.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger les résultats", csv, "resultats_transport.csv", "text/csv")
