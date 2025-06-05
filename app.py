import streamlit as st
import openrouteservice
import folium
from streamlit.components.v1 import html

st.set_page_config(page_title="Calcul Coûts Transport", layout="wide")

# --- CSS personnalisé ---
st.markdown("""
    <style>
    :root {
        --bleu-fonce: #0D1B2A;
        --rouge: #D90429;
        --blanc: #F0F0F0;
    }
    .main {
        background-color: var(--blanc);
        color: var(--bleu-fonce);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: var(--bleu-fonce);
        font-weight: 700;
    }
    .stTextInput > div > input,
    .stNumberInput > div > input {
        border: 2px solid var(--bleu-fonce);
        border-radius: 5px;
        padding: 6px 8px;
        color: var(--bleu-fonce);
        background-color: #fff;
    }
    button.stButton > button {
        background-color: var(--rouge);
        color: var(--blanc);
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
        border: none;
        transition: background-color 0.3s ease;
    }
    button.stButton > button:hover {
        background-color: #b00321;
        cursor: pointer;
    }
    table.result-table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 20px;
        font-size: 1rem;
    }
    table.result-table th, table.result-table td {
        border: 1.5px solid var(--bleu-fonce);
        padding: 8px 12px;
        text-align: left;
        color: var(--bleu-fonce);
    }
    table.result-table th {
        background-color: var(--rouge);
        color: var(--blanc);
    }
    .folium-map {
        border: 2px solid var(--bleu-fonce);
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Clé API OpenRouteService (mettre dans secrets ou variables d'environnement) ---
import os
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
        st.error(f"Erreur OpenRouteService : {e}")
        return None, None, None, None, None

def calcul_cout_transport(distance_km, duree_heure, nb_palettes):
    if distance_km is None or duree_heure is None:
        return None, None, None
    CK = 0.583  # €/km
    CC = 30.33  # €/h
    CJ = 250.63  # €/jour
    CG = 2.48   # €/h
    cout_total = distance_km * CK + duree_heure * CC + CJ + duree_heure * CG
    cout_palette = cout_total / nb_palettes if nb_palettes > 0 else None
    duree_totale = duree_heure  # ici on peut intégrer la logique temps de repos plus tard
    return round(cout_total, 2), round(cout_palette, 2), round(duree_totale, 2)

st.title("🚚 Estimation des coûts de transport (Frigo LD_EA)")

with st.form("formulaire_calcul"):
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("📍 Données du trajet")
        pays_dep = st.text_input("Pays de départ", value="France")
        ville_dep = st.text_input("Ville de départ", value="Givors")
        cp_dep = st.text_input("Code postal départ", value="69700")
        st.markdown("---")
        pays_arr = st.text_input("Pays d'arrivée", value="France")
        ville_arr = st.text_input("Ville d'arrivée", value="Le Luc")
        cp_arr = st.text_input("Code postal arrivée", value="83340")
        nb_palettes_form = st.number_input("Nombre de palettes", min_value=1, max_value=33, value=33)
        submitted = st.form_submit_button("📍 Calculer le transport")

    with col2:
        st.subheader("🗺️ Itinéraire")
        if 'm' in st.session_state:
            html(st.session_state.m._repr_html_(), height=500)

if submitted:
    adresse_dep = f"{cp_dep} {ville_dep}, {pays_dep}"
    adresse_arr = f"{cp_arr} {ville_arr}, {pays_arr}"

    with st.spinner("🛰️ Calcul en cours..."):
        dist, duree, coord_dep, coord_arr, route = get_distance_duration(adresse_dep, adresse_arr)
        cout_total, cout_palette, duree_totale = calcul_cout_transport(dist, duree, nb_palettes_form)

    if dist is not None:
        # Carte Folium
        midpoint = [(coord_dep[1] + coord_arr[1]) / 2, (coord_dep[0] + coord_arr[0]) / 2]
        m = folium.Map(location=midpoint, zoom_start=7)
        folium.Marker([coord_dep[1], coord_dep[0]], tooltip="Départ", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker([coord_arr[1], coord_arr[0]], tooltip="Arrivée", icon=folium.Icon(color='red')).add_to(m)
        coords_route = route['features'][0]['geometry']['coordinates']
        coords_route_latlon = [[pt[1], pt[0]] for pt in coords_route]
        folium.PolyLine(coords_route_latlon, color="blue", weight=5, opacity=0.7).add_to(m)

        st.session_state.m = m

        st.success("✅ Calcul terminé")

        # Stocker infos résultats pour l'affichage sous le formulaire
        st.session_state.resultats = {
            "Adresse départ": adresse_dep,
            "Adresse arrivée": adresse_arr,
            "Distance (km)": dist,
            "Durée estimée (h)": duree_totale,
            "Coût total (€)": cout_total,
            "Coût par palette (€)": cout_palette,
        }
    else:
        st.error("❌ Adresse non reconnue. Merci de vérifier les informations saisies.")

if 'resultats' in st.session_state:
    st.markdown("### Résultats du transport")
    # Affichage tableau HTML stylé
    result_html = """
    <table class="result-table">
        <thead>
            <tr>
                <th>Donnée</th><th>Valeur</th>
            </tr>
        </thead>
        <tbody>
    """
    for k, v in st.session_state.resultats.items():
        result_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
    result_html += "</tbody></table>"
    st.markdown(result_html, unsafe_allow_html=True)
