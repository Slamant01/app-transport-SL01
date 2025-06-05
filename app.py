import streamlit as st
import openrouteservice
import folium
from streamlit_folium import st_folium

# Configuration de la page
st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")
st.title("🚛 Estimation du coût de transport")

# Initialisation du client OpenRouteService
import os
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

# Fonctions
def get_coordinates(address):
    try:
        result = client.pelias_search(text=address)
        coords = result['features'][0]['geometry']['coordinates']  # lon, lat
        return [coords[1], coords[0]]  # lat, lon
    except Exception as e:
        st.error(f"Erreur de géocodage : {e}")
        return None

def get_distance_duration(coord_dep, coord_arr):
    try:
        route = client.directions((coord_dep[::-1], coord_arr[::-1]), profile='driving-hgv', format='geojson')
        segment = route['features'][0]['properties']['segments'][0]
        distance_km = segment['distance'] / 1000
        duration_h = segment['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2)
    except Exception as e:
        st.error(f"Erreur d'itinéraire : {e}")
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

# Interface utilisateur
with st.form("formulaire"):
    st.subheader("📝 Informations de transport")
    col1, col2 = st.columns(2)
    with col1:
        pays_dep = st.text_input("Pays de départ", value="France")
        ville_dep = st.text_input("Ville de départ", value="Givors")
        cp_dep = st.text_input("Code postal départ", value="69700")
    with col2:
        pays_arr = st.text_input("Pays d’arrivée", value="France")
        ville_arr = st.text_input("Ville d’arrivée", value="Le Luc")
        cp_arr = st.text_input("Code postal arrivée", value="83340")
    
    nb_palettes = st.number_input("Nombre de palettes", min_value=1, max_value=33, value=33)

    submitted = st.form_submit_button("Calculer")

