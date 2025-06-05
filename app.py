import streamlit as st
import openrouteservice
import pandas as pd
import time

st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")

# Clé API OpenRouteService (à mettre dans Secrets)
import os
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

def get_distance_duration(dep, arr):
    try:
        coord_dep = client.pelias_search(text=dep)['features'][0]['geometry']['coordinates']  # [lon, lat]
        coord_arr = client.pelias_search(text=arr)['features'][0]['geometry']['coordinates']
        route = client.directions([coord_dep, coord_arr], profile='driving-hgv', format='geojson')
        distance_km = route['features'][0]['properties']['segments'][0]['distance'] / 1000
        duration_h = route['features'][0]['properties']['segments'][0]['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2)
    except Exception as e:
        st.error(f"Erreur lors du calcul de l'itinéraire : {e}")
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

with st.form("form_transport"):
    pays_dep = st.text_input("Pays de départ", "France")
    ville_dep = st.text_input("Ville de départ", "Givors")
    cp_dep = st.text_input("Code postal de départ", "69700")

    pays_arr = st.text_input("Pays d'arrivée", "France")
    ville_arr = st.text_input("Ville d'arrivée", "Le Luc")
    cp_arr = st.text_input("Code postal d'arrivée", "83340")

    nb_palettes = st.number_input("Nombre de palettes (1 à 33)", min_value=1, max_value=33, value=33)

    submitted = st.form_submit_button("Calculer")

if submitted:
    adresse_dep = f"{cp_dep} {ville_dep} {pays_dep}"
    adresse_arr = f"{cp_arr} {ville_arr} {pays_arr}"

    distance, duree = get_distance_duration(adresse_dep, adresse_arr)
    cout_total, cout_par_palette = calcul_cout_transport(distance, duree, nb_palettes)

    if distance is not None and duree is not None:
        st.write(f"**Distance:** {distance} km")
        st.write(f"**Durée:** {duree} heures")
        st.write(f"**Coût total estimé:** {cout_total} €")
        st.write(f"**Coût par palette:** {cout_par_palette} €")
    else:
        st.error("Impossible de calculer l'itinéraire avec les adresses fournies. Veuillez vérifier les informations.")
