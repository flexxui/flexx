# MULTISITE CONTAINER
#
# DOCKER RUN ARGS
# --network=web
# --volume=/root/_flexx/demo:/root/flexx_demo
# --memory="256m"
# --cpus="0.5"
# --label="traefik.docker.network=web"
# --label="traefik.enable=true"
# --label="traefik.demoflexxapp.frontend.rule=Host:demo.flexx.app,demo1.flexx.app"
# --label="traefik.demoflexxapp.protocol=http"
# --label="traefik.demoflexxapp.port=80"

FROM python:3.6-alpine

RUN apk add --no-cache gcc g++ make linux-headers musl-dev libffi-dev openssl-dev git \
    && pip --no-cache-dir install psutil markdown tornado


WORKDIR /root
COPY . .

RUN pip --no-cache-dir install dialite webruntime pscript \
  && pip --no-cache-dir install https://github.com/flexxui/flexx/archive/master.zip

CMD python demo.py --flexx-hostname=0.0.0.0 --flexx-port=80
