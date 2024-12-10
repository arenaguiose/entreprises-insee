import streamlit as st
import pandas as pd
import math
from pathlib import Path
import datetime
import openpyxl
import plotly.express as px

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Entreprises créées en 2024 IDF",
    page_icon=":office:", # This is an emoji shortcode. Could be a URL too.
    layout="wide",
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_biz_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

                              
    # 1. Charger le fichier CSV avec des types de données précisés
    DATA_FILENAME = Path(__file__).parent/'data/etablissements-idf.csv'

    dtypes = {
        "siret": "string",
        "siren": "string",
        "codeCommuneEtablissement": "string",
        "activitePrincipaleEtablissement": "string",
        "activitePrincipaleUniteLegale": "string",
        "categorieJuridiqueUniteLegale": "string",
        "dateCreationEtablissement": "string",  # On peut le convertir en datetime plus tard
        "dateCreationUniteLegale": "string",
        "etatAdministratifEtablissement": "string",
        "etatAdministratifUniteLegale": "string",
        "codePostalEtablissement": "string",
        "coordonneeLambertAbscisseEtablissement": "string",  # Lire en tant que string pour nettoyer
        "coordonneeLambertOrdonneeEtablissement": "string",  # Lire en tant que string pour nettoyer
        "denominationUniteLegale": "string",
        "denominationUsuelleEtablissement": "string",
        "economieSocialeSolidaireUniteLegale": "string",
        "sexeUniteLegale": "string",
        "trancheEffectifsEtablissement": "string",
        "trancheEffectifsUniteLegale": "string",
        "categorieEntreprise": "string",
    }

 # Instead of a CSV on disk, you could read from an HTTP endpoint here too.

    raw_df = pd.read_csv(DATA_FILENAME, dtype=dtypes)


    # 2. Nettoyer les colonnes de coordonnées pour remplacer les valeurs non valides
    # Convertir en numérique après avoir remplacé les valeurs non numériques
    raw_df["coordonneeLambertAbscisseEtablissement"] = pd.to_numeric(raw_df["coordonneeLambertAbscisseEtablissement"].replace("[ND]", pd.NA), errors="coerce")
    raw_df["coordonneeLambertOrdonneeEtablissement"] = pd.to_numeric(raw_df["coordonneeLambertOrdonneeEtablissement"].replace("[ND]", pd.NA), errors="coerce")

    # 3. Sélectionner les colonnes utiles
    columns_to_keep = list(dtypes.keys())
    raw_df = raw_df[columns_to_keep]

    # 4. Conversion des dates en format datetime
    raw_df["dateCreationEtablissement"] = pd.to_datetime(raw_df["dateCreationEtablissement"], errors="coerce")
    raw_df["dateCreationUniteLegale"] = pd.to_datetime(raw_df["dateCreationUniteLegale"], errors="coerce")

    # 5. Remplacer les valeurs non valides (par exemple '[ND]') dans les colonnes catégoriques
    raw_df.replace({"[ND]": pd.NA, "null": pd.NA}, inplace=True)

    return raw_df


def get_naf_data():
    DATA_FILENAME = Path(__file__).parent/'data/naf_5_niveaux.csv'
    dtypes_naf = {
        "NIV1": "string",
        "NIV2": "string",
        "NIV3": "string",
        "NIV4": "string",
        "NIV5": "string",
        "NIV1 - Libellé": "string",
        "NIV2 - Libellé": "string", 
        "NIV3 - Libellé": "string",
        "NIV4 - Libellé": "string",
        "NIV5 - Libellé": "string"
    }
    # Lecture du fichier avec les dtypes définis
    raw_df_naf = pd.read_csv(DATA_FILENAME, dtype=dtypes_naf)
    return raw_df_naf

def get_cj_data():
    DATA_FILENAME = Path(__file__).parent/'data/cj_septembre_2022.xlsx'


    dtypes_cj = {
        "CJ1": "string",
        "CJ2": "string",
        "CJ3": "string",
        "CJ1 - Libellé": "string",
        "CJ2 - Libellé": "string", 
        "CJ3 - Libellé": "string"
    }

    # Lecture du fichier avec les dtypes définis
    raw_df_cj = pd.read_excel(DATA_FILENAME, dtype=dtypes_cj)

    return raw_df_cj


biz_df = get_biz_data()
naf_df = get_naf_data()
cj_df = get_cj_data()


# Effectuer la jointure
def get_work_data():
    raw_df_merged = biz_df.merge(naf_df, left_on=biz_df['activitePrincipaleUniteLegale'], right_on=naf_df['NIV5']).drop(columns=['key_0'])
    raw_df_merged = raw_df_merged.merge(cj_df, left_on=raw_df_merged['categorieJuridiqueUniteLegale'], right_on=cj_df['CJ3']).drop(columns=['key_0'])
    
    cols_to_clean = ["NIV1 - Libellé", "NIV2 - Libellé", "NIV3 - Libellé", "NIV4 - Libellé", "NIV5 - Libellé"]
    for col in cols_to_clean:
        raw_df_merged[col] = (
            raw_df_merged[col]
            .str.replace("'", "", regex=False)  # Supprimer les apostrophes
            .str.replace('"', '', regex=False)  # Supprimer les guillemets
        )
    return raw_df_merged

df = get_work_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :office: Entreprises créées en 2024 en IDF

Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
But it's otherwise a great (and did I mention _free_?) source of data.
'''

# Add some spacing
''
''

# Input dates
left, right = st.columns(2, vertical_alignment="bottom")
with left:
    min_value = df['dateCreationUniteLegale'].min()
    d1 = st.date_input("Date début", min_value)
with right:
    max_value = df['dateCreationUniteLegale'].max()
    d2 = st.date_input("Date fin", max_value)

# Options pour le contrôle segmenté
options = ["Sélectionner", "Exclure"]

# Liste des niveaux de NAF
naf_levels = [
    {"level": "NIV1", "label": "NIV1 - Libellé"},
    {"level": "NIV2", "label": "NIV2 - Libellé"},
    {"level": "NIV3", "label": "NIV3 - Libellé"},
    {"level": "NIV4", "label": "NIV4 - Libellé"},
    {"level": "NIV5", "label": "NIV5 - Libellé"},
]

# Dictionnaire pour stocker les sélections de chaque niveau
naf_selections = {}

# Créer une copie du DataFrame pour filtrage dynamique
filtered_df = df.copy()

# Générer dynamiquement les widgets pour chaque niveau NAF
for i, naf in enumerate(naf_levels):
    level = naf["level"]
    label = naf["label"]

    # Obtenir les options disponibles dynamiquement
    if i == 0:  # Premier niveau : pas de filtre parent
        available_options = filtered_df[label].drop_duplicates().sort_values()
    else:  # Filtrer selon les niveaux précédents
        parent_level = naf_levels[i - 1]["label"]
        parent_selected = naf_selections[f"selected_{naf_levels[i - 1]['level']}"]
        if parent_selected:
            filtered_df = filtered_df[filtered_df[parent_level].isin(parent_selected)]
        available_options = filtered_df[label].drop_duplicates().sort_values()

    # Layout en deux colonnes
    left, right = st.columns([3, 6], vertical_alignment="bottom")

    with left:
        # Contrôle segmenté pour le niveau
        naf_selections[f"selection_{level}"] = st.segmented_control(
            f"NAF - {level}",
            options,
            key=f"segmented_control_{level}",
            selection_mode="single",
            default="Sélectionner"
        )
    with right:
        # Multiselect pour les libellés correspondants
        naf_selections[f"selected_{level}"] = st.multiselect(
            "",
            available_options,
            key=f"multiselect_{level}"
        )

# Liste des niveaux de CJ
cj_levels = [
    {"level": "CJ1", "label": "CJ1 - Libellé"},
    {"level": "CJ2", "label": "CJ2 - Libellé"},
    {"level": "CJ3", "label": "CJ3 - Libellé"},
]

# Dictionnaire pour stocker les sélections de chaque niveau
cj_selections = {}

# Créer une copie du DataFrame pour filtrage dynamique CJ
filtered_df_cj = df.copy()

# Générer dynamiquement les widgets pour chaque niveau CJ
for i, cj in enumerate(cj_levels):
    level = cj["level"]
    label = cj["label"]

    # Obtenir les options disponibles dynamiquement
    if i == 0:  # Premier niveau : pas de filtre parent
        available_options = filtered_df_cj[label].drop_duplicates().sort_values()
    else:  # Filtrer selon les niveaux précédents
        parent_level = cj_levels[i - 1]["label"]
        parent_selected = cj_selections[f"selected_{cj_levels[i - 1]['level']}"]
        if parent_selected:
            filtered_df_cj = filtered_df_cj[filtered_df_cj[parent_level].isin(parent_selected)]
        available_options = filtered_df_cj[label].drop_duplicates().sort_values()

    # Layout en deux colonnes
    left, right = st.columns([3, 6], vertical_alignment="bottom")

    with left:
        # Contrôle segmenté pour le niveau
        cj_selections[f"selection_{level}"] = st.segmented_control(
            f"CJ - {level}",
            options,
            key=f"segmented_control_cj_{level}",
            selection_mode="single",
            default="Sélectionner"
        )
    with right:
        # Multiselect pour les libellés correspondants
        cj_selections[f"selected_{level}"] = st.multiselect(
            "",
            available_options,
            key=f"multiselect_cj_{level}"
        )

# Appliquer tous les filtres
filtered_df = df.copy()

# Appliquer les filtres NAF
for naf in naf_levels:
    level = naf["level"]
    label = naf["label"]
    selected_values = naf_selections[f"selected_{level}"]
    if naf_selections[f"selection_{level}"] == "Sélectionner" and selected_values:
        filtered_df = filtered_df[filtered_df[label].isin(selected_values)]
    elif naf_selections[f"selection_{level}"] == "Exclure" and selected_values:
        filtered_df = filtered_df[~filtered_df[label].isin(selected_values)]

# Appliquer les filtres CJ
for cj in cj_levels:
    level = cj["level"]
    label = cj["label"]
    selected_values = cj_selections[f"selected_{level}"]
    if cj_selections[f"selection_{level}"] == "Sélectionner" and selected_values:
        filtered_df = filtered_df[filtered_df[label].isin(selected_values)]
    elif cj_selections[f"selection_{level}"] == "Exclure" and selected_values:
        filtered_df = filtered_df[~filtered_df[label].isin(selected_values)]

# Compter le nombre d'entreprises restantes
num_enterprises = filtered_df["siret"].nunique()

# Afficher le résultat
st.metric("Nombre d'entreprises", num_enterprises)


# Agrégation : compter le nombre d'entreprises par NIV1 et NIV2
naf_counts = filtered_df.groupby(["NIV1 - Libellé", "NIV2 - Libellé"]).size().reset_index(name="Count")

# Maintenant, vous devez préparer les données pour l'affichage
# Créez une colonne avec les codes NAF de niveau 1 pour chaque ligne
naf_counts["NIV1 - Libellé"] = naf_counts["NIV1 - Libellé"].astype(str)

# Création du graphique en barres horizontal avec la répartition du niveau 2
# Utilisation de st.bar_chart

# D'abord, on crée un pivot pour avoir une colonne par code NAF de niveau 2
pivot_df = naf_counts.pivot_table(index="NIV1 - Libellé", columns="NIV2 - Libellé", values="Count", aggfunc="sum", fill_value=0)

# Affichage du graphique
st.bar_chart(pivot_df, use_container_width=True, horizontal=True)