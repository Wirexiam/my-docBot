FROM python:3.13

WORKDIR /opt/app

ENV HOME=/tmp/libreoffice_user
ENV USER=1001

COPY requirements.txt .

RUN pip install --no-cache-dir virtualenv && \
    python -m virtualenv /opt/venv

# RUN apt-get update && apt-get install -y \
#     libreoffice-java-common \
#     libreoffice


RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

RUN apt install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng libgl1

COPY . .

RUN chown -R 1001:1001 /opt/app

# RUN mkdir -p /tmp/libreoffice_user /tmp/.cache/dconf \
#     && chown -R 1001:1001 /tmp/libreoffice_user /tmp/.cache/dconf \
#     && chmod -R 777 /tmp/libreoffice_user /tmp/.cache/dconf

USER 1001

CMD ["/opt/venv/bin/python", "main.py"]