FROM python:3.9.0

ADD kitchen.py .

RUN pip install requests flask

EXPOSE 3030

CMD ["python","-u","kitchen.py"]