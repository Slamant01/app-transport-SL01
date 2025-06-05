import streamlit as st
import openrouteservice
import os

# Configuration de la page
st.set_page_config(page_title="Calcul Coûts Transport", layout="centered")

# Clé API OpenRouteService depuis secrets
ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)

# Fonction pour obtenir les coordonnées à partir d'une adresse
def get_coordinates(adresse):
    try:
        result = client.pelias_search(text=adresse)
        coords = result['features'][0]['geometry']['coordinates']
        return coords[::-1]  # retourne (lat, lon)
    except:
        return None

# Fonction pour calculer distance et durée
def get_distance_duration(coord_dep, coord_arr):
    try:
        route = client.directions((coord_dep, coord_arr), profile='driving-hgv', format='geojson')
        distance_km = route['features'][0]['properties']['segments'][0]['distance'] / 1000
        duration_h = route['features'][0]['properties']['segments'][0]['duration'] / 3600
        return round(distance_km, 2), round(duration_h, 2)
    except:
        return None, None

# Fonction pour calculer le coût de transport
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

# Titre
st.title("🚛 Estimation des Coûts de Transport (Frigo LD_EA)")

# Formulaire de saisie
with st.form("formulaire"):
    st.subheader("📍 Adresse de départ")
    pays_dep = st.text_input("Pays de départ", "France")
    ville_dep = st.text_input("Ville de départ", "Givors")
    cp_dep = st.text_input("Code postal de départ", "69700")

    st.subheader("🏁 Adresse d'arrivée")
    pays_arr = st.text_input("Pays d'arrivée", "France")
    ville_arr = st.text_input("Ville d'arrivée", "Le Luc")
    cp_arr = st.text_input("Code postal d'arrivée", "83340")

    st.subheader("📦 Données de transport")
    nb_palettes = st.number_input("Nombre de palettes", min_value=1, max_value=33, value=33)

    submitted = st.form_submit_button("🔍 Calculer")

# Traitement une fois le formulaire soumis
if submitted:
    with st.spinner("⏳ Traitement en cours..."):
        adresse_dep = f"{cp_dep} {ville_dep}, {pays_dep}"
        adresse_arr = f"{cp_arr} {ville_arr}, {pays_arr}"
        
        coord_dep = get_coordinates(adresse_dep)
        coord_arr = get_coordinates(adresse_arr)

        if coord_dep and coord_arr:
            distance, duree = get_distance_duration(coord_dep, coord_arr)
            cout_total, cout_palette = calcul_cout_transport(distance, duree, nb_palettes)

            if distance and duree:
                st.success("✅ Calcul terminé")
                st.write(f"📍 **Départ :** {adresse_dep}")
                st.write(f"🏁 **Arrivée :** {adresse_arr}")
                st.write(f"🛣️ **Distance :** {distance} km")
                st.write(f"⏱️ **Durée estimée :** {duree} h")
                st.write(f"💶 **Coût total :** {cout_total} €")
                st.write(f"📦 **Coût par palette :** {cout_palette} €")
            else:
                st.error("❌ Impossible de calculer la distance ou la durée.")
        else:
            st.error("❌ Échec de géocodage. Vérifiez les adresses saisies.")
