#! /bin/bash

cd $(dirname $0)

FOLDER=.venv-timelapse

python -m venv ${FOLDER}

. ./${FOLDER}/bin/activate

pythom -m pip install --upgrade pip
pythom -m pip install -r requirements.txt

# Hint how to activate
echo . ./${FOLDER}/bin/activate