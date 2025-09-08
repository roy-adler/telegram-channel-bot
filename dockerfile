FROM python:3.12-slim
WORKDIR /app
COPY bot.py .
RUN pip install --no-cache-dir python-telegram-bot[webhooks]==21.4
ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]