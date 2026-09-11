import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
from datetime import date
import json

st.set_page_config(page_title="Toronto Satellite Viewer", layout="wide")
st.title("🛰️ Toronto Satellite Imagery Viewer")
st.write(
    "This app shows real satellite photos of the Toronto area, taken by the "
    "Sentinel-2 satellite. Pick a date range below and click Get Image."
)

key_dict = json.loads(st.secrets["EE_SERVICE_ACCOUNT_KEY"])
credentials = ee.ServiceAccountCredentials(
    key_dict["client_email"], key_data=st.secrets["EE_SERVICE_ACCOUNT_KEY"]
)
ee.Initialize(credentials)

def add_ee_layer(self, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
    ).add_to(self)

folium.Map.add_ee_layer = add_ee_layer

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("Start date", value=date(2025, 12, 1))
with col2:
    end = st.date_input("End date", value=date(2026, 2, 28))

cloud_limit = st.slider("Maximum cloudiness allowed (%)", 0, 100, 20)
run = st.button("Get Image")

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
            m = folium.Map(location=[43.70, -79.38], zoom_start=10)
            m.add_ee_layer(composite, vis_params, "Toronto (RGB)")
            folium.LayerControl().add_to(m)
            st_folium(m, width=1200, height=600)
else:
    st.info("Choose your dates above and click Get Image to load the map.")

st.markdown("---")
st.caption("Data source: Copernicus Sentinel-2, via Google Earth Engine.")
