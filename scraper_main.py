import subprocess
from subprocess import PIPE
import os
import threading

# cwd not currently showing up in shells spawned..
cwd = os.getcwd()

scripts = [
    r"/home/pi/PythonProjects/Botcheck/bike.sh",
    r"/home/pi/PythonProjects/Botcheck/micro.sh",
]


def launch_script(script: str):
    commands = [
        r"bash",
        r"-i",  # leaving off -x option for now
        script,
        "shell=True",
        "stdin=PIPE",
        "stdout=PIPE",
        "stderr=PIPE",
        "cwd=" + cwd,
        "start_new_session=True",
        "universal_newlines=True",
    ]
    pro = subprocess.run(commands)
    print(pro.returncode)


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
