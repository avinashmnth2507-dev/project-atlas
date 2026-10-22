FROM python:3.14.9-slim-trixie@sha256:0214bda9af2652a418f2bf34373a4d3ca00a5f4784081e040049433ac9cc79d5

ENV FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/atlas

WORKDIR /opt/atlas

COPY app/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --no-compile -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY --chown=10001:10001 app/src/atlas ./atlas

USER 10001:10001

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:5000/health', timeout=2).read()"]

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--worker-class", "sync", "--no-control-socket", "--access-logfile", "-", "--error-logfile", "-", "atlas:create_app()"]
