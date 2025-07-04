import streamlit as st
import openrouteservice
import pandas as pd
import time
import folium
from streamlit.components.v1 import html
import os

st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")

# Clé API OpenRouteService (à mettre dans Secrets)
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

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
    """
    Ajoute les temps de pause, repos, chargement et déchargement :
    - 45 min de pause toutes les 4h30 de conduite
    - 11h de repos si durée > 9h
    - 45 min de chargement + 45 min de déchargement (1.5h)
    """
    temps_pause = 0
    temps_repos = 0
    temps_chargement_dechargement = 1.5  # 45 min + 45 min

    # Pauses : 45 min (0.75h) toutes les 4.5h de conduite
    nb_pauses = int(duree_heure // 4.5)
    temps_pause = nb_pauses * 0.75

    duree_totale = duree_heure + temps_pause + temps_chargement_dechargement

    # Repos journalier : si durée totale > 9h, ajouter 11h de repos
    if duree_totale > 9:
        temps_repos = 11
        duree_totale += temps_repos

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
            dist, duree, coord_dep, coord_arr, route = get_distance_duration(adresse_dep, adresse_arr)
            cout_total, cout_palette, duree_totale = calcul_cout_transport(dist, duree, nb_palettes_form)

        if dist is not None:
            st.success("✅ Calcul terminé")
            st.markdown(f"""
                - **Adresse départ** : {adresse_dep}  
                - **Adresse arrivée** : {adresse_arr}  
                - **Distance** : {dist} km  
                - **Durée estimée (conduite)** : {duree} h  
                - **Durée totale (avec pauses, chargement/déchargement, repos)** : {duree_totale} h  
                - **Coût total** : {cout_total} €  
                - **Coût par palette** : {cout_palette} €
            """)

            midpoint = [(coord_dep[1] + coord_arr[1]) / 2, (coord_dep[0] + coord_arr[0]) / 2]
            m = folium.Map(location=midpoint, zoom_start=7)

            folium.Marker([coord_dep[1], coord_dep[0]], tooltip="Départ", icon=folium.Icon(color='green')).add_to(m)
            folium.Marker([coord_arr[1], coord_arr[0]], tooltip="Arrivée", icon=folium.Icon(color='red')).add_to(m)

            coords_route = route['features'][0]['geometry']['coordinates']
            coords_route_latlon = [[pt[1], pt[0]] for pt in coords_route]
            folium.PolyLine(coords_route_latlon, color="blue", weight=5, opacity=0.7).add_to(m)

            html_map = m._repr_html_()
            html(html_map, height=500)
        else:
            st.error("❌ Adresse non reconnue. Merci de vérifier les informations saisies.")
