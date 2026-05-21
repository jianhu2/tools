FROM debian:bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MAX_UPLOAD_MB=50 \
    WATERMARK_FONT_PATH=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

RUN printf 'deb http://mirrors.tencentyun.com/debian bookworm main\ndeb http://mirrors.tencentyun.com/debian bookworm-updates main\ndeb http://mirrors.tencentyun.com/debian-security bookworm-security main\n' > /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        fonts-noto-cjk \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
        -i http://mirrors.tencentyun.com/pypi/simple \
        --trusted-host mirrors.tencentyun.com \
        -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
