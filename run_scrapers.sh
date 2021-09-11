#!/usr/bin/bash
cd /home/pi/PythonProjects/Botcheck
source ./venv/bin/activate
pip install -r ./requirements.txt
chmod 755 ./scraper_main.py
python3 ./scraper_main.py
