FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /app
EXPOSE 8501 8000
CMD streamlit run ride_3d_viewer.py --server.port=8501 --server.headless=true
