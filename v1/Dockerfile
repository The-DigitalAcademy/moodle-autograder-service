   FROM python:3.11-slim

   WORKDIR /app

   COPY . /app

   RUN apt-get update && apt-get install -y \
        cmake \
        g++ \
        git \
        && apt-get clean

        RUN pip install --upgrade pip
   RUN pip install wheel setuptools pip --upgrade 
   RUN pip install git+https://github.com/ageitgey/face_recognition_models --verbose
   RUN pip install git+https://github.com/davisking/dlib.git@master

   RUN pip install Flask
   RUN pip install flask_cors
   RUN pip install pillow
   RUN pip install numpy
   RUN pip install psycopg2-binary
   RUN pip install -r requirements.txt
   RUN pip install python-dotenv


   EXPOSE 5000

   ENV PYTHONUNBUFFERED=1

   ENV FLASK_ENV=production

   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "480", "app:app"]