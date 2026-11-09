FROM python:3.12-slim
WORKDIR /app
COPY server.py ./server.py
COPY data/ ./data/
ENV PYTHONUNBUFFERED=1
EXPOSE 8028
CMD ["python", "server.py"]
