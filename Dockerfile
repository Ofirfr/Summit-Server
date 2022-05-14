FROM ubuntu

#Install python
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip

# Add docker-compose-wait tool
ENV WAIT_VERSION 2.7.2
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait

WORKDIR /src/source-code

#Install dependencies
RUN pip install flask
RUN pip install flask-restful
RUN pip install bcrypt
RUN pip install psycopg2-binary
RUN pip install docker
COPY . /src/source-code

#ENTRYPOINT python3 server.py
