FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /workdir
WORKDIR /workdir
COPY requirements.txt /workdir/
RUN pip install --upgrade pip wheel
RUN pip install -r requirements.txt
COPY . /workdir/

CMD ["python", "main.py"]
