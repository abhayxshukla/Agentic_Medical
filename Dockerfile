# ---------- Stage 1: build ----------
FROM python:3.12.9 AS build
WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libzbar0 \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && pip install --upgrade pip setuptools wheel \
    && pip install --upgrade transformers \
    && pip install --timeout=100 -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------- Stage 2: runtime ----------
FROM python:3.12.9-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libzbar0 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app

ENV PYTHONWARNINGS="ignore::DeprecationWarning"
EXPOSE 5005

CMD ["python", "main.py"]
    