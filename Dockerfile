FROM sebp/elk
MAINTAINER Justin Littman <justinlittman@gwu.edu>

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python-dev \
    libffi-dev \
    libssl-dev \
    python-pip \
    git \
    wget
#Need newer version of jq
WORKDIR /usr/bin
RUN wget https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && mv jq-linux64 jq && chmod +x jq
#pip set in 7.1.2
# Easy installing pip since there is a problem with the pip version currently available from apt.
RUN easy_install pip==7.1.2
#RUN pip install pip==7.1.2
#RUN pip install --upgrade pip
#Avoid the warning of https
RUN pip install --upgrade ndg-httpsclient
RUN pip install appdeps
ENV SFM_REQS release
ENV DEBUG false
ADD https://raw.githubusercontent.com/gwu-libraries/sfm-utils/master/docker/base/setup_reqs.sh /opt/sfm-setup/
ADD docker/start.sh /usr/local/bin/sfm_elk_start.sh
RUN chmod +x /usr/local/bin/sfm_elk_start.sh

ADD . /opt/sfm-elk/
WORKDIR /opt/sfm-elk
RUN pip install -r requirements/common.txt -r requirements/release.txt

ENTRYPOINT ["/usr/local/bin/sfm_elk_start.sh"]
