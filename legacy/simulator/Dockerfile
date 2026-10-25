FROM python:3.11-slim

WORKDIR /app

COPY services/simulator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services /app/services
COPY simulator /app/simulator

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "services/simulator/scada_simulator.py"]
