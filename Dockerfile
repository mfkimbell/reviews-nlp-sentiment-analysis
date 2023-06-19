FROM debian:bookworm-slim AS getdoppler
RUN apt-get update
RUN apt-get install git curl wget gnupg busybox-static -y
RUN (curl -Ls https://cli.doppler.com/install.sh || wget -qO- https://cli.doppler.com/install.sh) | sh


FROM python:3.9-slim AS pybuilder
ARG DOPPLER_TOKEN

COPY --from=getdoppler /usr/bin/doppler /usr/bin/

RUN python -m pip --no-cache-dir install pdm
RUN pdm config python.use_venv false

COPY pyproject.toml pdm.lock /project/

WORKDIR /project
RUN doppler run -- pdm install --prod --no-lock --no-editable -vv


FROM python:3.9-slim
ENV PYTHONPATH=/project/pkgs
COPY --from=getdoppler /usr/bin/doppler /usr/bin/
COPY --from=getdoppler /usr/bin/busybox /usr/bin/
COPY --from=pybuilder /project/__pypackages__/3.9/lib /project/pkgs
# COPY --from=jsbuilder /project/build /project/publicp

# ADD config.yml /project/local_config.yml

WORKDIR /project

ADD src/ /project/pkgs/
ADD local_config.yml /project/local_config.yml
# ADD config.yml /local_config.yml

EXPOSE 5000

ENTRYPOINT ["doppler", "run", "--", "python", "pkgs/edit_twitter_database/__main__.py"]
CMD []
