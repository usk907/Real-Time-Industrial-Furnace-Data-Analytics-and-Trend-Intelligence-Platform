FROM python:3.11-slim

WORKDIR /app

COPY simulator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY simulator /app/simulator

ENV PYTHONUNBUFFERED=1

CMD ["python", "simulator/scada_simulator.py"]
