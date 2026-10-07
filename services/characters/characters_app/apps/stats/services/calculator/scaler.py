import math

class StatScaler:
    """Пропорциональное масштабирование текущих значений при изменении максимумов."""

    @staticmethod
    def scale(current: float, old_max: float, new_max: float, is_increasing: bool) -> float:
        """
        Масштабирует текущее значение пропорционально изменению максимума.
        
        Например: было 50/100 HP (50%), максимум стал 120 → станет 60 HP (50%).
        При увеличении максимума округляем вверх (math.ceil).
        При уменьшении — вниз (math.floor), но не больше нового максимума.
        """
        if old_max == 0:
            return 0
        if old_max == new_max:
            return current
        ratio = current / old_max
        if is_increasing:
            return min(math.ceil(ratio * new_max), new_max)
        else:
            scaled = math.floor(ratio * new_max)
            return min(scaled, new_max)