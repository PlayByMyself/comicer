#!/bin/bash
set -e

USERNAME=comicer
PUID=${PUID:-1000}
PGID=${PGID:-1000}

groupmod -o -g "${PGID}" "${USERNAME}"
usermod -o -u "${PUID}" "${USERNAME}"
exec gosu "${USERNAME}" "$@"
