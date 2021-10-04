FROM python:3.9-slim

ENV \
    TERM=xterm-256color \
    \
    # Don't periodically check PyPI to determine whether a new version of pip is available for download.
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    # Disable package cache.
    PIP_NO_CACHE_DIR=off \
    # Python won’t try to write .pyc files on the import of source modules.
    PYTHONDONTWRITEBYTECODE=on \
    # install a handler for SIGSEGV, SIGFPE, SIGABRT, SIGBUS and SIGILL signals to dump the Python traceback
    PYTHONFAULTHANDLER=on \
    # Force the stdout and stderr streams to be unbuffered.
    PYTHONUNBUFFERED=on \
    # set workdir as PYTHONPATH
    PYTHONPATH=/opt/app \
    TZ=Europe/Moscow \
    TOKEN="TOKEN" \
    MAX_SLOTS=100

STOPSIGNAL SIGINT

RUN mkdir /app
WORKDIR /app
RUN pip install  -Ur  /app/requirements.txt
COPY . /app/

ENTRYPOINT ['python', 'bot.py']