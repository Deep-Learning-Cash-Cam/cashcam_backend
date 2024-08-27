FROM python:3.11

COPY . .
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]