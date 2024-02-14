FROM python:3.8-slim

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .

EXPOSE 4105

CMD ["waitress-serve", "--listen=0.0.0.0:4105", "app:app"]
