#!/usr/bin/bash
cd /home/pi/PythonProjects/Botcheck
source ./venv/bin/activate
pip install -r ./requirements.txt
python3 ./scrape_bike.py
