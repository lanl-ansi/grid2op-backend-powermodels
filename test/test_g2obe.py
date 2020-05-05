#!/usr/bin/env python3

exec(open("../PowerModelsBackend.py").read())

pmbe = PowerModelsBackend()
print("\n")

pmbe.load_grid(path="data", filename="case5.m")

result = pmbe.runpf()
print("runpf ac result: {}".format(result))

result = pmbe.runpf(is_dc=True)
print("runpf dc result: {}".format(result))
