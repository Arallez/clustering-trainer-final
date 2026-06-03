FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /usr/sbin/nologin sandbox

WORKDIR /opt/sandbox

COPY sandbox/requirements.txt /opt/sandbox/requirements.txt
RUN pip install --no-cache-dir -r /opt/sandbox/requirements.txt

COPY sandbox/runner.py /opt/sandbox/runner.py

USER sandbox
WORKDIR /workspace

ENTRYPOINT ["python", "/opt/sandbox/runner.py"]
