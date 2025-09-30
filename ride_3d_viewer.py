import streamlit as st
import streamlit.components.v1 as components
import json
import os
import uuid
import subprocess
import atexit
import logging
from dotenv import load_dotenv
from fit_to_czml import FitToCzml

class RideViewerManager:
    def __init__(self, output_dir="ride_html", port=8000, token=""):
        self.output_dir = output_dir
        self.port = port
        self.token = token
        self.server = None
        os.makedirs(self.output_dir, exist_ok=True)
        self._start_server_once()

    def _start_server_once(self):
        if self.server is None:
            self.server = subprocess.Popen(
                ["python", "-m", "http.server", str(self.port)],
                cwd=self.output_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            atexit.register(self.stop)

    def stop(self):
        if self.server:
            self.server.terminate()
            self.server = None

    def save_html(self, czml):
        uid = uuid.uuid4().hex[:8]
        filename = f"ride_{uid}.html"
        path = os.path.join(self.output_dir, filename)

        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
        czml_json = json.dumps(czml, ensure_ascii=False)
        html = template.replace("__CZML_DATA__", czml_json)
        html = html.replace("__ACCESS_TOKEN__", self.token)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return f"http://localhost:{self.port}/{filename}"

def setup_logger(name=__name__):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
load_dotenv()
logger = setup_logger("RideAnimationGenerator")


if "viewer" not in st.session_state:
    try:
        cesium_token = os.getenv("CESIUM_TOKEN") or st.secrets["CESIUM_TOKEN"]
    except Exception as e:
        st.warning(f"Fail to get CESIUM_TOKEN: {e}")
        cesium_token = ""
    
    try:
        viewer = RideViewerManager(token=cesium_token)
        st.session_state["viewer"] = viewer
    except Exception as e:
        st.error(f"Failed to initialize RideViewerManager: {e}")
        st.stop()

viewer = st.session_state["viewer"]
st.title("Ride CesiumJS Viewer")

uploaded_file = st.file_uploader("Upload FIT file", type=["fit"])
step = st.number_input("step（sec）", min_value=1, value=60, step=10)

if uploaded_file:
    try:
        converter = FitToCzml(uploaded_file, step=step)
        converter.parse()
        czml = converter.build()
        url = viewer.save_html(czml)
        logger.info(f"Generated HTML URL: {url}")
        st.success("3D ride visualization generated successfully!")
        st.markdown(f"[show this ride.]({url})", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")
