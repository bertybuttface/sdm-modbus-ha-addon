# https://developers.home-assistant.io/docs/add-ons/configuration#add-on-dockerfile
ARG BUILD_FROM
FROM $BUILD_FROM

# Execute during the build of the image
ARG TEMPIO_VERSION BUILD_ARCH
RUN \
    curl -sSLf -o /usr/bin/tempio \
    "https://github.com/home-assistant/tempio/releases/download/${TEMPIO_VERSION}/tempio_${BUILD_ARCH}"

# Install requirements for add-on
RUN \
  apk add --no-cache \
    g++ \
    python3 \
    python3-dev \
    py3-pip \
    zeromq-dev

# Copy requirements
COPY rootfs/requirements.txt /requirements.txt

RUN \
  pip3 install -r /requirements.txt

# Copy root filesystem
COPY rootfs /
