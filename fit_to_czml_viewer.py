import streamlit as st
import json
from fit_to_czml import FitToCzml

st.title("FIT to CZML Viewer")

uploaded_file = st.file_uploader("Upload FIT file", type=["fit"])
step = st.number_input("setep（sec）", min_value=1, value=60)

if uploaded_file:
    try:
        converter = FitToCzml(uploaded_file, step=step)
        converter.parse()
        czml = converter.build()
        st.success("Convert to CZML sccess！")
        st.code(json.dumps(czml, indent=2), language="json", height=300)
        st.download_button("Download CZML", data=json.dumps(czml,indent=2), file_name="ride.czml", mime="application/json")
    except Exception as e:
        st.error(f"error!: {e}")
