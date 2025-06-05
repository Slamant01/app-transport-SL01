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
        # Recherche des coordonnées
        coord_dep = client.pelias_search(text=dep)['features'][0]['geometry']['coordinates']  # [lon, lat]
        coord_arr = client.pelias_search(text=arr)['features'][0]['geometry']['coordinates']  # [lon, lat]

        # Appel de l’API directions
        route = client.directions(
            coordinates=[coord_dep, coord_arr],
            profile='driving-hgv',
            format='geojson'
        )
        distance_km = route['features'][0]['properties']['segments'][0]['distance'] / 1000
        duration_h = route['features'][0]['properties']['segments'][0]['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2)
    except Exception as e:
        print("Erreur OpenRouteService :", e)
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
st.subheader("✍️ Calcul manuel d’un transport")

with st.form("formulaire_calcul"):
    col1, col2 = st.columns(2)
    with col1:
        pays_dep = st.text_input("Pays de départ", value="France")
        ville_dep = st.text_input("Ville de départ", value="Givors")
        cp_dep = st.text_input("Code postal départ", value="69700")
    with col2:
        pays_arr = st.text_input("Pays d'arrivée", value="France")
        ville_arr = st.text_input("Ville d'arrivée", value="Le Luc")
        cp_arr = st.text_input("Code postal arrivée", value="83340")

    nb_palettes_form = st.number_input("Nombre de palettes", min_value=1, max_value=33, value=33)

    submitted = st.form_submit_button("📍 Calculer le transport")

    if submitted:
        adresse_dep = f"{cp_dep} {ville_dep}, {pays_dep}"
        adresse_arr = f"{cp_arr} {ville_arr}, {pays_arr}"

        with st.spinner("🛰️ Calcul en cours..."):
            dist, duree = get_distance_duration(adresse_dep, adresse_arr)
            cout_total, cout_palette = calcul_cout_transport(dist, duree, nb_palettes_form)

        if dist is not None:
            st.success("✅ Calcul terminé")
            st.markdown(f"""
                - **Adresse départ** : {adresse_dep}  
                - **Adresse arrivée** : {adresse_arr}  
                - **Distance** : {dist} km  
                - **Durée estimée** : {duree} h  
                - **Coût total** : {cout_total} €  
                - **Coût par palette** : {cout_palette} €
            """)
        else:
            st.error("❌ Adresse non reconnue. Merci de vérifier les informations saisies.")
