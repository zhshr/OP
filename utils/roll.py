import random
from enum import IntEnum


def roll(exp: str) -> list[int]:
    comp = exp.split('d')
    if len(comp) == 1:
        result = [random.randint(1, int(comp[0]))]
    elif comp[0] == '':
        result = [random.randint(1, int(comp[1]))]
    else:
        result = [random.randint(1, int(comp[1])) for i in range(int(comp[0]))]
    return result


class SuccessLevel(IntEnum):
    CRITICAL_SUCCESS = 6,
    EXTREME_SUCCESS = 5,
    HARD_SUCCESS = 4,
    REGULAR_SUCCESS = 3,
    FAILURE = 2,
    CRITICAL_FAILURE = 1

    def display_name(self):
        match self:
            case SuccessLevel.CRITICAL_SUCCESS:
                return "完美成功"
            case SuccessLevel.EXTREME_SUCCESS:
                return "极大成功"
            case SuccessLevel.HARD_SUCCESS:
                return "大成功"
            case SuccessLevel.REGULAR_SUCCESS:
                return "成功"
            case SuccessLevel.FAILURE:
                return "失败"
            case SuccessLevel.CRITICAL_FAILURE:
                return "大失败"


def success_level(dice: int, level: int) -> SuccessLevel:
    if dice == 1:
        return SuccessLevel.CRITICAL_SUCCESS
    elif dice <= level/5:
        return SuccessLevel.EXTREME_SUCCESS
    elif dice <= level/2:
        return SuccessLevel.HARD_SUCCESS
    elif dice <= level:
        return SuccessLevel.REGULAR_SUCCESS
    elif dice <= 95:
        return SuccessLevel.FAILURE
    else:
        return SuccessLevel.CRITICAL_FAILURE
