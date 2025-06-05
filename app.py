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

if submitted:
    adresse_dep = f"{cp_dep} {ville_dep}, {pays_dep}"
    adresse_arr = f"{cp_arr} {ville_arr}, {pays_arr}"
    
    coord_dep = get_coordinates(adresse_dep)
    coord_arr = get_coordinates(adresse_arr)

    if coord_dep and coord_arr:
        distance, duree = get_distance_duration(coord_dep, coord_arr)
        cout_total, cout_palette = calcul_cout_transport(distance, duree, nb_palettes)

        st.success("✅ Calcul terminé")
        st.write(f"📍 **Adresse départ :** {adresse_dep}")
        st.write(f"📍 **Adresse arrivée :** {adresse_arr}")
        st.write(f"🛣️ **Distance :** {distance} km")
        st.write(f"⏱️ **Durée estimée :** {duree} h")
        st.write(f"💶 **Coût total :** {cout_total} €")
        st.write(f"📦 **Coût par palette :** {cout_palette} €")

        # Affichage de la carte
        st.subheader("🗺️ Visualisation sur carte")
        lat_centre = (coord_dep[0] + coord_arr[0]) / 2
        lon_centre = (coord_dep[1] + coord_arr[1]) / 2
        m = folium.Map(location=[lat_centre, lon_centre], zoom_start=7)
        folium.Marker(coord_dep, tooltip="Départ", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(coord_arr, tooltip="Arrivée", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine([coord_dep, coord_arr], color="blue", weight=4).add_to(m)
        st_folium(m, height=450)
