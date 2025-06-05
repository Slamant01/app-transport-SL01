import streamlit as st
import openrouteservice
import os

# Configuration de la page
st.set_page_config(page_title="Calcul Coûts Transport", layout="centered")

# Clé API
ORS_API_KEY = os.getenv("ORS_API_KEY")
if not ORS_API_KEY:
    st.error("🔐 Clé API OpenRouteService manquante dans secrets.")
    st.stop()

client = openrouteservice.Client(key=ORS_API_KEY)

# Fonctions
def get_coordinates(adresse):
    try:
        result = client.pelias_search(text=adresse)
        if not result['features']:
            return None
        coords = result['features'][0]['geometry']['coordinates']
        return coords[::-1]  # (lat, lon)
    except Exception as e:
        st.warning(f"Erreur lors du géocodage de '{adresse}' : {e}")
        return None

def get_distance_duration(coord_dep, coord_arr):
    try:
        route = client.directions((coord_dep, coord_arr), profile='driving-hgv', format='geojson')
        segment = route['features'][0]['properties']['segments'][0]
        distance_km = segment['distance'] / 1000
        duration_h = segment['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2)
    except Exception as e:
        st.warning(f"Erreur lors du calcul de l'itinéraire : {e}")
        return None, None

def calcul_cout_transport(distance_km, duree_heure, nb_palettes):
    if distance_km is None or duree_heure is None:
        return None, None
    CK = 0.60   # €/km
    CC = 28.96  # €/h
    CJ = 260.35 # €/jour
    CG = 3.05   # €/h
    cout_total = distance_km * CK + duree_heure * CC + CJ + duree_heure * CG
    cout_palette = cout_total / nb_palettes if nb_palettes > 0 else None
    return round(cout_total, 2), round(cout_palette, 2)

# Interface utilisateur
st.title("🚛 Estimation des Coûts de Transport (Frigo LD_EA)")

with st.form("formulaire"):
    st.subheader("📍 Adresse de départ")
    pays_dep = st.text_input("Pays de départ", "France")
    ville_dep = st.text_input("Ville de départ", "Givors")
    cp_dep = st.text_input("Code postal de départ", "69700")

    st.subheader("🏁 Adresse d'arrivée")
    pays_arr = st.text_input("Pays d'arrivée", "France")
    ville_arr = st.text_input("Ville d'arrivée", "Le Luc")
    cp_arr = st.text_input("Code postal d'arrivée", "83340")

    st.subheader("📦 Transport")
    nb_palettes = st.number_input("Nombre de palettes", min_value=1, max_value=33, value=33)

    submitted = st.form_submit_button("🔍 Calculer")

if submitted:
    with st.spinner("🧭 Calcul en cours..."):
        adresse_dep = f"{cp_dep} {ville_dep}, {pays_dep}"
        adresse_arr = f"{cp_arr} {ville_arr}, {pays_arr}"

        st.write(f"🔍 Adresse départ : `{adresse_dep}`")
        st.write(f"🔍 Adresse arrivée : `{adresse_arr}`")

        coord_dep = get_coordinates(adresse_dep)
        coord_arr = get_coordinates(adresse_arr)

        if coord_dep is None:
            st.error(f"❌ Adresse de départ non localisée : {adresse_dep}")
        elif coord_arr is None:
            st.error(f"❌ Adresse d’arrivée non localisée : {adresse_arr}")
        else:
            distance, duree = get_distance_duration(coord_dep, coord_arr)
            if distance is None or duree is None:
                st.error("❌ Impossible de calculer la distance ou la durée.")
            else:
                cout_total, cout_palette = calcul_cout_transport(distance, duree, nb_palettes)

                st.success("✅ Résultat du calcul")
                st.markdown(f"""
                - **Distance :** {distance} km  
                - **Durée :** {duree} h  
                - **Coût total :** {cout_total} €  
                - **Coût par palette :** {cout_palette} €
                """)
