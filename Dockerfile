FROM python:3


COPY assistant.py /app/
COPY requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "/app/assistant.py"]
