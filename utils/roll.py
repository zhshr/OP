import random


def roll(exp: str) -> list[int]:
    comp = exp.split('d')
    if len(comp) == 1:
        result = [random.randint(1, int(comp[0]))]
    elif comp[0] == '':
        result = [random.randint(1, int(comp[1]))]
    else:
        result = [random.randint(1, int(comp[1])) for i in range(int(comp[0]))]
    return result
