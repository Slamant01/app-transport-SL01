import streamlit as st
import openrouteservice
import pandas as pd
import folium
from streamlit.components.v1 import html
import os

st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")

# Clé API OpenRouteService (à mettre dans les secrets)
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

# Tableau de dégressivité (facteurs k)
facteur_k = {
    1: 1.00, 2: 0.88, 3: 0.80, 4: 0.74, 5: 0.70, 6: 0.66, 7: 0.63, 8: 0.60, 9: 0.58, 10: 0.56,
    11: 0.54, 12: 0.52, 13: 0.50, 14: 0.49, 15: 0.48, 16: 0.47, 17: 0.46, 18: 0.45, 19: 0.44, 20: 0.43,
    21: 0.42, 22: 0.41, 23: 0.40, 24: 0.39, 25: 0.38, 26: 0.37, 27: 0.36, 28: 0.35, 29: 0.34, 30: 0.33,
    31: 0.32, 32: 0.31, 33: 0.30
}

def get_distance_duration(dep, arr):
    try:
        coord_dep = client.pelias_search(text=dep)['features'][0]['geometry']['coordinates']
        coord_arr = client.pelias_search(text=arr)['features'][0]['geometry']['coordinates']
        route = client.directions(
            coordinates=[coord_dep, coord_arr],
            profile='driving-hgv',
            format='geojson'
        )
        distance_km = route['features'][0]['properties']['segments'][0]['distance'] / 1000
        duration_h = route['features'][0]['properties']['segments'][0]['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2), coord_dep, coord_arr, route
    except Exception as e:
        print("Erreur OpenRouteService :", e)
        return None, None, None, None, None

def ajouter_temps_pause_et_repos(duree_heure):
    temps_pause = int(duree_heure // 4.5) * 0.75
    temps_repos = 11 if (duree_heure + temps_pause) > 9 else 0
    temps_chargement = 0.75
    temps_dechargement = 0.75
    duree_totale = duree_heure + temps_pause + temps_repos + temps_chargement + temps_dechargement
    return round(duree_totale, 2)

def calcul_cout_transport(distance_km, duree_heure, nb_palettes):
    if distance_km is None or duree_heure is None:
        return None, None, None

    CK = 0.583  # €/km
    CC = 30.33  # €/h
    CJ = 250.63  # €/jour
    CG = 2.48   # €/h

    duree_totale = ajouter_temps_pause_et_repos(duree_heure)
    cout_total = distance_km * CK + duree_totale * CC + CJ + duree_totale * CG
    cout_palette = cout_total / nb_palettes if nb_palettes > 0 else None

    return round(cout_total, 2), round(cout_palette, 2), duree_totale

# Interface utilisateur
st.title("🚚 Estimation des coûts de transport (Frigo LD_EA)")
st.subheader("✍️ Calcul manuel d’un transport")

with st.form("formulaire_calcul_
