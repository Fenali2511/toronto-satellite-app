import streamlit as st
import ee
import geemap.foliumap as geemap
from datetime import date

# Page setup
st.set_page_config(page_title="Toronto Satellite Viewer", layout="wide")
st.title("🛰️ Toronto Satellite Imagery Viewer")
st.write(
    "This app shows real satellite photos of the Toronto area, taken by the "
    "Sentinel-2 satellite. Pick a date range and click Get Image."
)

# Earth Engine connection — see Part D below for why this differs from Colab
import json
key_dict = json.loads(st.secrets["EE_SERVICE_ACCOUNT_KEY"])
credentials = ee.ServiceAccountCredentials(key_dict["client_email"], key_data=st.secrets["EE_SERVICE_ACCOUNT_KEY"])
ee.Initialize(credentials)

# User controls
col1, col2 = st.columns(2)
with col1:
    start = st.date_input("Start date", value=date(2025, 12, 1))
with col2:
    end = st.date_input("End date", value=date(2026, 2, 28))

cloud_limit = st.slider("Maximum cloudiness allowed (%)", 0, 100, 20)
run = st.button("Get Image")

# Fetch and display
if run:
    with st.spinner("Fetching satellite imagery..."):
        toronto_aoi = ee.Geometry.Rectangle([-79.64, 43.58, -79.12, 43.86])
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(toronto_aoi)
            .filterDate(str(start), str(end))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_limit))
        )
        count = collection.size().getInfo()
        if count == 0:
            st.error("No images matched. Try widening dates or raising cloud %.")
        else:
            st.success(f"Found {count} matching images.")
            composite = collection.median().clip(toronto_aoi)
            vis_params = {"min": 0, "max": 3000, "bands": ["B4", "B3", "B2"]}
            m = geemap.Map()
            m.centerObject(toronto_aoi, 10)
            m.addLayer(composite, vis_params, "Toronto (RGB)")
            m.to_streamlit(height=600)