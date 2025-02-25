import subprocess
import sys

message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Update"

commands = [
    "git add .",
    f'git commit -m "{message}"',
    "git push"
]

for cmd in commands:
    subprocess.run(cmd, shell=True, check=True)
