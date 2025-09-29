from fitparse import FitFile
from datetime import datetime, timezone
from io import BytesIO
import base64

class FitToCzml:
    def __init__(self, fit_input, step=60):
        if isinstance(fit_input, (str, BytesIO)):
            self.fit = FitFile(fit_input)
        else:
            raise TypeError("fit_input must be a file path or BytesIO object")
        self.step = step
        self.records = []

    def parse(self):
        for i, record in enumerate(self.fit.get_messages("record")):
            if i % self.step != 0:
                continue
            try:
                ts = record.get_value("timestamp")
                lat = record.get_value("position_lat")
                lon = record.get_value("position_long")
                alt = record.get_value('enhanced_altitude') or record.get_value('altitude') or 0
                if ts is None or lat is None or lon is None:
                    continue
                timestamp = ts.replace(tzinfo=timezone.utc)
                self.records.append((timestamp, lat, lon, alt))
            except Exception as e:
                raise ValueError(f"Failed to parse record {i}: {e}")

    def build(self):
        if not self.records:
            raise ValueError("No records parsed. Run parse() first.")
        self.records.sort(key=lambda x: x[0])
        epoch = self.records[0][0]
        czml = [
            {
                "id": "document",
                "version": "1.0",
                "clock": {
                    "interval": f"{self.records[0][0].isoformat()}/{self.records[-1][0].isoformat()}",
                    "currentTime": self.records[0][0].isoformat(),
                    "multiplier": 60,
                    "range": "LOOP_STOP"
                }
            },
            {
                "id": "ride",
                "name": "ride",
                "availability": f"{self.records[0][0].isoformat()}/{self.records[-1][0].isoformat()}",
                "position": {
                    "interpolationAlgorithm": "LINEAR",
                    "interpolationDegree": 1,
                    "referenceFrame": "FIXED",
                    "epoch": epoch.isoformat(),
                    "cartographicDegrees": []
                },
                "billboard": {
                    "image": self._svg_base64(),
                    "scale": 0.5,
                    "verticalOrigin": "BOTTOM",
                    "heightReference": "CLAMP_TO_GROUND"
                }
            }
        ]

        for ts, lat, lon, alt in self.records:
            offset = (ts - epoch).total_seconds()
            czml[1]["position"]["cartographicDegrees"].extend([
                round(offset, 2),
                round(self._semicircle_to_deg(lon), 8),
                round(self._semicircle_to_deg(lat), 8),
                round(alt, 2)
            ])

        return czml

    # Convert SEMICIRCLE to DEG
    def _semicircle_to_deg(self, val):
        return val * (180 / 2**31)

    def _svg_base64(self):
        svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#0000ff"><circle cx="12" cy="12" r="10"/></svg>"""
        encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{encoded}"
