FROM python:3.12

WORKDIR /opt/app



COPY requirements.txt .

RUN pip install --no-cache-dir virtualenv && \
    python -m virtualenv /opt/venv

RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R 1001:1001 /opt/app
USER 1001

CMD ["/opt/venv/bin/python", "main.py"]