FROM ubuntu:18.04

RUN apt-get update \
&& apt-get install -y python3.6 \
&& apt-get install -y python3-pip \
&& apt-get install -y mysql-client \
&& apt-get install -y libmysqlclient-dev \
&& apt-get install -y wget \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* \
&& cd /usr/local/bin \
&& ln -s /usr/bin/python3 python \
&& pip3 install --upgrade pip

COPY ./requirements.txt /root/requirements.txt
RUN pip3 install -r /root/requirements.txt

# work directory
ENV POC_BASE_ROOT=/usr/local/poc_base
COPY . ${POC_BASE_ROOT}
WORKDIR ${POC_BASE_ROOT}

ENV PYTHONPATH="${PYTHONPATH}:${POC_BASE_ROOT}/app:${POC_BASE_ROOT}/framework" \
    GRPC_ERROR_LOG="/var/log/grpc_server_error.log" \
    GRPC_LOG="/var/log/grpc_server.log" \
    GRPC_MAX_WORKERS=10 \
    GRPC_PID_FILE="/var/run/poc_base.pid"

# Compile .proto file
# RUN wget https://raw.githubusercontent.com/podder-ai/pipeline-framework/master/modules/app/api/protos/pipeline_framework.proto -P ${POC_BASE_ROOT}/framework/api/protos/
RUN python ./run_codegen.py

RUN chmod +x ./scripts/entrypoint.sh
ENTRYPOINT ["./scripts/entrypoint.sh"]