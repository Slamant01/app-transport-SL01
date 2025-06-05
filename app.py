import streamlit as st
import openrouteservice
import folium
from streamlit.components.v1 import html
import os

st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")

# CSS pour style compact, bordures, couleurs bleu foncé / rouge / blanc, et titre petit
st.markdown("""
<style>
/* Réduction des marges/paddings pour compacter le formulaire */
label, .stTextInput, .stNumberInput {
    margin-bottom: 4px !important;
    padding-bottom: 0px !important;
}
.css-1d391kg > div {
    margin-bottom: 6px !important;
}
/* Style du titre */
.main-title {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
    margin-top: 10px;
    color: #0D3B66; /* Bleu foncé */
}
/* Bordure et style du formulaire */
.form-container {
    border: 1px solid #0D3B66; /* Bleu foncé */
    border-radius: 8px;
    padding: 15px;
    background-color: #F0F4F8; /* Blanc cassé */
}
/* Style labels section */
.section-label {
    font-weight: 600;
    color: #0D3B66;
    margin-bottom: 8px;
}
/* Résultats style */
.results {
    margin-top: 20px;
    border: 1px solid #D72631; /* Rouge */
    border-radius: 6px;
    padding: 15px;
    background-color: white;
    color: #0D3B66;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Clé API OpenRouteService
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

def calcul_cout_transport(distance_km, duree_heure, nb_palettes):
    if distance_km is None or duree_heure is None:
        return None, None
    CK = 0.583  # €/km
    CC = 30.33  # €/h
    CJ = 250.63  # €/jour
    CG = 2.48   # €/h
    cout_total = distance_km * CK + duree_heure * CC + CJ + duree_heure * CG
    cout_palette = cout_total / nb_palettes if nb_palettes > 0 else None
    return round(cout_total, 2), round(cout_palette, 2)

# --- Interface ---

st.markdown('<h3 class="main-title">🚚 Estimation des coûts de transport (Frigo LD_EA)</h3>', unsafe_allow_html=True)
st.markdown('<p style="margin-top: -10px; margin-bottom: 10px; font-weight: 400; color: #555;">✍️ Calcul manuel d’un transport</p>', unsafe_allow_html=True)

with st.form("formulaire_calcul"):
    col_form, col_map = st.columns([1,1.2])

    with col_form:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        st.markdown('<div class="section-label">Point de départ</div>', unsafe_allow_html=True)
        pays_dep = st.text_input("Pays de départ", value="France", key="pays_dep")
        ville_dep = st.text_input("Ville de départ", value="Givors", key="ville_dep")
        cp_dep = st.text_input("Code postal départ", value="69700", key="cp_dep")

        st.markdown('<div class="section-label" style="margin-top:15px;">Point d\'arrivée</div>', unsafe_allow_html=True)
        pays_arr = st.text_input("Pays d'arrivée", value="France", key="pays_arr")
        ville_arr = st.text_input("Ville d'arrivée", value="Le Luc", key="ville_arr")
        cp_arr = st.text_input("Code postal arrivée", value="83340", key="cp_arr")

        nb_palettes_form = st.number_input("Nombre de palettes", min_value=1, max_value=33, value=33, key="nb_palettes")

        submitted = st.form_submit_button("📍 Calculer le transport")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_map:
        # Place pour la carte (sera affichée après calcul)
        map_placeholder = st.empty()

if submitted:
    adresse_dep = f"{cp_dep} {ville_dep}, {pays_dep}"
    adresse_arr = f"{cp_arr} {ville_arr}, {pays_arr}"

    with st.spinner("🛰️ Calcul en cours..."):
        dist, duree, coord_dep, coord_arr, route = get_distance_duration(adresse_dep, adresse_arr)
        cout_total, cout_palette = calcul_cout_transport(dist, duree, nb_palettes_form)

    if dist is not None:
        # Afficher résultats sous la zone formulaire + carte
        st.markdown(f"""
        <div class="results">
        <p><b>Adresse départ :</b> {adresse_dep}</p>
        <p><b>Adresse arrivée :</b> {adresse_arr}</p>
        <p><b>Distance :</b> {dist} km</p>
        <p><b>Durée estimée :</b> {duree} h</p>
        <p><b>Coût total :</b> {cout_total} €</p>
        <p><b>Coût par palette :</b> {cout_palette} €</p>
        </div>
        """, unsafe_allow_html=True)

        # Création de la carte folium
        midpoint = [(coord_dep[1] + coord_arr[1]) / 2, (coord_dep[0] + coord_arr[0]) / 2]
        m = folium.Map(location=midpoint, zoom_start=7)
        folium.Marker([coord_dep[1], coord_dep[0]], tooltip="Départ", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker([coord_arr[1], coord_arr[0]], tooltip="Arrivée", icon=folium.Icon(color='red')).add_to(m)
        coords_route = route['features'][0]['geometry']['coordinates']
        coords_route_latlon = [[pt[1], pt[0]] for pt in coords_route]
        folium.PolyLine(coords_route_latlon, color="blue", weight=5, opacity=0.7).add_to(m)

        html_map = m._repr_html_()
        map_placeholder.html(html_map, height=500)
    else:
        st.error("❌ Adresse non reconnue. Merci de vérifier les informations saisies.")
