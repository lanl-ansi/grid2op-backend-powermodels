#!/usr/bin/env python3

import sys
import subprocess


print("starting julia...")
julia_process = subprocess.Popen(
    "julia -e 'include(\"TestBackend.jl\"); interactive_mode()'",
    shell=True,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
)


while True:
    sys.stdout.flush()
    julia_process.stdout.flush()
    output = julia_process.stdout.readline()
    if output.startswith("waiting for input line...") or julia_process.poll() is not None:
        break
    if output:
        print(output.strip())
print("julia process ready for input")




def run_julia_backend_command(julia_process, command):
    if julia_process.poll() is not None:
        print("process has terminated skipping julia command: ", command)

    print("sending command to julia: {}".format(command))
    sys.stdout.flush()
    sys.stderr.flush()

    julia_process.stdin.write(command)
    julia_process.stdin.write("\n")
    julia_process.stdin.flush()

    results = []
    while True:
        sys.stdout.flush()
        output = julia_process.stdout.readline()
        if output.startswith("waiting for input line...") or julia_process.poll() is not None:
            break
        else:
            results.append(output.strip())

    print("julia command complete")

    if len(results) != 2:
        print("\033[91mbad backend output, incorrect number of lines, {}\033[0m".format(len(results)))
        return []

    if results[1] != "complete":
        print("\033[91mbad backend output, status value {}, see process stderr for details\033[0m".format(results[1]))
        return []

    return results[0]


result = run_julia_backend_command(julia_process, "get_value")
result = run_julia_backend_command(julia_process, "set_foo")
result = run_julia_backend_command(julia_process, "get_value")
result = run_julia_backend_command(julia_process, "bloop")
result = run_julia_backend_command(julia_process, "set_bar")
result = run_julia_backend_command(julia_process, "get_value")
result = run_julia_backend_command(julia_process, "set_value, something")
result = run_julia_backend_command(julia_process, "get_value")
result = run_julia_backend_command(julia_process, "shutdown")


# julia_process.stdin.close()
# julia_process.terminate()


print("julia stderr:")
sys.stdout.flush()
sys.stderr.flush()
outputs = julia_process.stderr.readlines()
for output in outputs:
    sys.stderr.write('\033[91m julia:\033[0m {}'.format(output))
