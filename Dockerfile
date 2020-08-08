FROM continuumio/anaconda3:4.4.0
LABEL Lucas B., https://github.com/ltbatista
COPY ./app /usr/local/python
EXPOSE 5000
WORKDIR /usr/local/python/
RUN pip install -r requirements.txt 
CMD python text_cluster_api.py