FROM alpine:3.19.2
RUN apk add python3 py3-pip
ENTRYPOINT sh -c "source .venv/bin/activate && exec python3 -m service -r ${RPC_HOST} -g ${GAME_HOST} -p ${PORT_RANGE} -j ${JWT_SECRET} -c /certificates/ssl.crt -k /certificates/ssl.key"

# Install Python dependencies
COPY --chown=root:root requirements.txt /opt/game/
WORKDIR /opt/game/
RUN python3 -m venv .venv \
 && source .venv/bin/activate \
 && pip3 install -r requirements.txt

# Install service and server
COPY --chown=root:root server/ /opt/game/server/
COPY --chown=root:root service/ /opt/game/service/

# Install tools for debugging
COPY --chown=root:root tools /opt/game/tools/
