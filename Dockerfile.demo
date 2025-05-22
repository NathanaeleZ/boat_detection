FROM python:3.10

WORKDIR /code

RUN apt-get update && apt-get install -y libgl1

COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./tests /code/tests

WORKDIR /code/tests

CMD ["python3","satellite.py"]