# mypaas.service = flexx.demo
#
# mypaas.url = https://demo.flexx.app
# mypaas.url = https://demo1.flexx.app
#
# mypaas.scale = 0
# mypaas.maxmem = 256m

FROM ubuntu:20.04

RUN apt update \
    && apt install -y python3-pip \
    && pip3 --no-cache-dir install pip --upgrade \
    && pip3 --no-cache-dir install psutil markdown tornado

WORKDIR /root
COPY . .

RUN pip3 --no-cache-dir install dialite webruntime pscript \
  && pip3 --no-cache-dir install https://github.com/flexxui/flexx/archive/master.zip

CMD ["python3", "demo.py", "--flexx-hostname=0.0.0.0", "--flexx-port=80"]
