FROM python:3.10-slim

# Install git and clone noVNC
RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/novnc/noVNC.git ./novnc

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
