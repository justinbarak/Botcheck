# syntax=docker/dockerfile:1

FROM  python:3.8

EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3","-u","/app/scrapemicrosoft.py"]

# "-u" is required to allow the print statements from the script to be read

# docker build --tag python-microdock --platform linux/amd64,linux/arm64,linux/arm/v7 .

# docker run -d -p 5000:5000 python-microdock


# $ export DOCKER_CLI_EXPERIMENTAL=enabled

# $ echo '{ "experimental": "enabled" }' >~/.docker/config.json

# $ cd "C:\Users\Gamer\PythonProjects\Botcheck"

# $ docker buildx create --driver docker-container \
# > --name container default

# docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t python-microdock:buildx --output type=tar,dest=./builds/myimage.tar .

# $ scp  "C:/Users/Gamer/PythonProjects/Botcheck/builds/myimage.tar" pi@192.168.1.29:docker_images/

# On RPi: $ docker import "/home/pi/docker_images/myimage.tar"