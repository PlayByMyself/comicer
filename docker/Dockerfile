FROM python:3.11-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    APP_PATH="/app" \
    VENV_PATH="/app/.venv" \
    AM_I_IN_A_DOCKER_CONTAINER=true
ENV PATH="$VENV_PATH/bin:$PATH"
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && apt-get install -y --no-install-recommends libglib2.0-0 \               
         libnss3 \                                     
         libnspr4 \                                    
         libatk1.0-0 \                                 
         libatk-bridge2.0-0 \                          
         libcups2 \                                    
         libdrm2 \                                     
         libdbus-1-3 \                                 
         libatspi2.0-0 \                               
         libx11-6 \                                    
         libxcomposite1 \                              
         libxdamage1 \                                 
         libxext6 \                                    
         libxfixes3 \                                  
         libxrandr2 \                                  
         libgbm1 \                                     
         libxcb1 \                                     
         libxkbcommon0 \                               
         libpango-1.0-0 \                              
         libcairo2 \                                   
         libasound2 \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove
    

FROM python-base as build-whl
ENV POETRY_VERSION=1.3.1
RUN --mount=type=cache,mode=0777,target=/root/.cache pip install poetry==$POETRY_VERSION
WORKDIR $APP_PATH
COPY . .
RUN --mount=type=cache,mode=0777,target=/root/.cache poetry install --only main --no-interaction
RUN poetry build

FROM python-base as install-whl
WORKDIR $APP_PATH/dist
COPY --from=build-whl $APP_PATH/dist/*.whl .
RUN python -m venv $VENV_PATH
RUN --mount=type=cache,mode=0777,target=/root/.cache python -m pip install $(ls *.whl | tail -n 1)


FROM python-base as prod
ENV DEFAULT_USER=comicer
ENV DEFAULT_UID=1000
ENV DEFAULT_GID=1000
RUN groupadd -g $DEFAULT_GID ${DEFAULT_USER} && \
    useradd --system -m -s /bin/bash -u ${DEFAULT_UID} -g ${DEFAULT_GID} ${DEFAULT_USER} && \
    mkdir /comic && \
    chown ${DEFAULT_USER}:${DEFAULT_USER} /comic
COPY --from=install-whl $VENV_PATH $VENV_PATH
COPY ./docker/entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
