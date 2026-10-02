import streamlit as st
import rasterio
from rasterio.transform import from_gcps
from rasterio.control import GroundControlPoint
import numpy as np
import pandas as pd
import os

st.set_page_config(page_title="GéoRéférenceur Express", layout="wide")

st.title("🌍 Application de Géoréférencement")
st.write("Transformez vos images simples en GeoTIFF en quelques clics.")

# 1. Chargement de l'image
uploaded_file = st.file_uploader("Choisissez une image (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Affichage de l'image pour repérer les pixels
    st.image(uploaded_file, caption="Image source", use_column_width=True)
    
    st.sidebar.header("Paramètres de géoréférencement")
    crs_input = st.sidebar.text_input("Système de coordonnées (CRS)", "EPSG:4326")
    
    st.subheader("Entrée des Points de Calage (GCP)")
    st.info("Entrez au moins 3 points. (X, Y) sont les pixels, (Lon, Lat) sont les coordonnées réelles.")
    
    # Tableau interactif pour les points
    data = {
        'Pixel_X': [0.0, 100.0, 100.0],
        'Pixel_Y': [0.0, 0.0, 100.0],
        'Lon_Dest': [0.0, 1.0, 1.0],
        'Lat_Dest': [0.0, 0.0, -1.0]
    }
    df = pd.DataFrame(data)
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("Générer le GeoTIFF"):
        try:
            # Conversion de l'image en array
            from PIL import Image
            img = Image.open(uploaded_file)
            img_array = np.array(img)
            
            # Gestion des dimensions (H, W, Bands)
            if len(img_array.shape) == 3:
                img_array = img_array.transpose(2, 0, 1) # Rasterio veut (Bands, H, W)
                count = img_array.shape[0]
            else:
                img_array = np.expand_dims(img_array, axis=0)
                count = 1
                
            height, width = img_array.shape[1], img_array.shape[2]

            # Création des GCPs pour Rasterio
            gcps = [
                GroundControlPoint(row['Pixel_Y'], row['Pixel_X'], row['Lon_Dest'], row['Lat_Dest'])
                for _, row in edited_df.iterrows()
            ]

            # Calcul de la transformation affine
            transform = from_gcps(gcps)

            # Sauvegarde temporaire du fichier
            output_path = "output_georef.tif"
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=count,
                dtype=img_array.dtype,
                crs=crs_input,
                transform=transform,
            ) as dst:
                dst.write(img_array)

            st.success("✅ Géoréférencement réussi !")
            
            # Bouton de téléchargement
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Télécharger le GeoTIFF",
                    data=f,
                    file_name="image_georeferencee.tif",
                    mime="image/tiff"
                )
        except Exception as e:
            st.error(f"Erreur : {e}")