FROM ubuntu:18.04

RUN apt-get update \
&& apt-get install -y python3.6 \
&& apt-get install -y python3-pip \
&& apt-get install -y mysql-client \
&& apt-get install -y libmysqlclient-dev \
&& apt-get install -y vim wget git unzip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

COPY ./requirements /root/requirements
COPY scripts/requirements.sh /requirements.sh
RUN chmod +x /requirements.sh
RUN /requirements.sh

ENV AIRFLOW_USER=airflow
ENV AIRFLOW_ROOT=/usr/local/airflow_root
ENV AIRFLOW_HOME=${AIRFLOW_ROOT}/airflow
ENV MODULES_PATH=${AIRFLOW_ROOT}/modules
ENV WEB_PATH=${AIRFLOW_ROOT}/web
ENV CLI_PATH=${AIRFLOW_ROOT}/cli
ENV STUB_PATH=${AIRFLOW_ROOT}/stub

# Add linux user.
RUN useradd -ms /bin/bash -d ${AIRFLOW_ROOT} -G sudo ${AIRFLOW_USER}

COPY ./airflow/dags ${AIRFLOW_HOME}/dags
COPY ./modules ${MODULES_PATH}
COPY ./web ${WEB_PATH}
COPY ./cli ${CLI_PATH}
COPY ./stub ${STUB_PATH}
COPY ./config ${AIRFLOW_ROOT}/config
RUN chown -R ${AIRFLOW_USER}.${AIRFLOW_USER} ${AIRFLOW_ROOT}

# Generate proto file and compile it
WORKDIR ${AIRFLOW_ROOT}
COPY ./scripts/build_proto_file.py ${AIRFLOW_ROOT}/scripts/
COPY ./pipeline.yml ${AIRFLOW_ROOT}/pipeline.yml
COPY ./run_codegen.py ${AIRFLOW_ROOT}
RUN python3 ${AIRFLOW_ROOT}/scripts/build_proto_file.py
RUN python3 ${AIRFLOW_ROOT}/run_codegen.py

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY mysql/my.conf /my.conf
RUN chmod +x /my.conf

EXPOSE 5000 8080

USER ${AIRFLOW_USER}
WORKDIR ${AIRFLOW_ROOT}
ENTRYPOINT ["/entrypoint.sh"]
