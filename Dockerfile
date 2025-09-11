FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install shadowsocks-libev and supervisor
RUN apt-get update && apt-get install -y \
    shadowsocks-libev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create shadowsocks config
RUN echo '{ \
    "server": "35.204.105.5", \
    "server_port": 23415, \
    "local_address": "127.0.0.1", \
    "local_port": 1080, \
    "password": "p1zsciXdqxcIJWqKvIb4TC", \
    "timeout": 300, \
    "method": "chacha20-ietf-poly1305" \
}' > /etc/shadowsocks.json

# Create supervisor config to run both shadowsocks and bot
RUN echo '[supervisord] \n\
nodaemon=true \n\
logfile=/var/log/supervisord.log \n\
\n\
[program:shadowsocks] \n\
command=ss-local -c /etc/shadowsocks.json \n\
autostart=true \n\
autorestart=true \n\
priority=1 \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
\n\
[program:bot] \n\
command=python -m src.main \n\
autostart=true \n\
autorestart=true \n\
priority=10 \n\
startsecs=5 \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
environment=USE_PROXY="true",PROXY_URL="socks5://127.0.0.1:1080"' > /etc/supervisor/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]