import subprocess
from subprocess import PIPE
import os
import threading

# cwd not currently showing up in shells spawned..
cwd = os.getcwd()

scripts = [
    r"/home/pi/PythonProjects/Botcheck/scrapemicrosoft.py",
    r"/home/pi/PythonProjects/Botcheck/scrape_bike.py",
]


def launch_script(script: str):
    # os.system(script)
    # exec(open(script).read())
    request = "chmod +x " + script + "; python3 " + script
    subprocess.call(request, shell=True)
    return None


# Thread objects
scriptThreads = []
for script in scripts:
    thisThread = threading.Thread(target=launch_script, args=(script,), kwargs=None)
    scriptThreads.append(thisThread)
    print(f"launching {script}")
    thisThread.start()
    print(f"launched {script}")

for thread in scriptThreads:
    thread.join()
print("finished")
