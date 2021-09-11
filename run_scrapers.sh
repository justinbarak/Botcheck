#!/usr/bin/bash

cat >scriptB <<EOF
#!/usr/bin/bash
source /home/pi/PythonProjects/Botcheck/venv/bin/activate
pip install -r requirements.txt
python3 scrape_bike.py
EOF
chmod +x scriptB

lxterminal --title="ScrapeMicrosoft" \
    -e "cat >scriptA <<EOF
#!/bin/sh
source /home/pi/PythonProjects/Botcheck/venv/bin/activate
pip install -r requirements.txt
python3 scrapemicrosoft.py
EOF
chmod +x scriptA
bash scriptA; bash"
lxterminal --title="ScrapeBikeSite" \
    -e "bash scriptB; bash"
