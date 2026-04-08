class CalculationService:
    """
    Расчёты по формулам Excel.

    Ключевая логика (на примере февраля):

    Первая таблица (строки 8-35, колонки A-I):
      C = odometer_end_day  — Спидометр конец дня (ввод, может быть пустым)
      D = distance_km       — Пробег путевка (ввод)
      E = fuel_waybill      — Бензин путевка (расчёт)
      F = odometer_start    — Спидометр начало (расчёт)
      G = odometer_end      — Спидометр конец (расчёт)
      H = fuel_remaining    — Бензин остаток (расчёт)
      I = fuel_received     — Бензин получено (ввод)

    Вторая таблица (отчёт, строки 46-73):
      I_отчёт = km_za_den   — «За день км» (промежуточный расчёт)

    Порядок расчёта каждого дня:
      1. km_za_den = calculate_km_za_den(C, D, max_prev_G)
      2. E = ROUND(km_za_den * fuel_rate / 100, 3)
      3. F = max_prev_G  (MAX всех предыдущих G; для первого дня = initial_odometer)
      4. G = F + km_za_den
      5. H = H_prev если km_za_den==0, иначе H_prev - E + I
    """

    @staticmethod
    def calculate_km_za_den(odometer_end_day, distance_km, max_prev_odometer_end):
        """
        «За день км» из отчёта (колонка I отчёта).
        Excel: =IF(AND(D=0,C=0), 0, IF(AND(C>0,D=0), C-MAX(G_prev), D))

        odometer_end_day  — C (спидометр конец дня, может быть None/0)
        distance_km       — D (пробег путевки, может быть None/0)
        max_prev_odometer_end — MAX всех предыдущих G (спидометр конец)
        """
        C = odometer_end_day or 0.0
        D = distance_km or 0.0

        if D == 0 and C == 0:
            return 0.0
        if C > 0 and D == 0:
            return C - max_prev_odometer_end
        return D

    @staticmethod
    def calculate_fuel_waybill(km_za_den, fuel_rate):
        """
        Бензин путевка (колонка E).
        Excel: =IF(I_отчёт=0, 0, ROUND(I_отчёт * P4 / 100, 3))
        """
        if km_za_den == 0:
            return 0.0
        return round(km_za_den * fuel_rate / 100, 3)

    @staticmethod
    def calculate_fuel_remaining(prev_fuel_remaining, fuel_waybill, fuel_received, km_za_den):
        """
        Бензин остаток (колонка H).
        Excel: =IF(I_отчёт=0, H_prev, H_prev - E + I)

        Если пробега нет (выходной), остаток не меняется.
        """
        if km_za_den == 0:
            return prev_fuel_remaining
        received = fuel_received or 0.0
        return prev_fuel_remaining - fuel_waybill + received

    @staticmethod
    def recalculate_from(records, start_index, initial_odometer, initial_fuel, fuel_rate):
        """
        Пересчитать записи начиная с start_index.

        records          — список DailyRecord, отсортированный по дню
        start_index      — индекс первой записи для пересчёта
        initial_odometer — E4 (спидометр начало месяца)
        initial_fuel     — K4 (остаток бензина начало месяца)
        fuel_rate        — P4 (норма расхода л/100км)
        """
        # Собираем MAX G от всех записей ДО start_index
        # (они уже посчитаны и не меняются)
        if start_index == 0:
            max_odometer_end = initial_odometer
            prev_fuel_remaining = initial_fuel
        else:
            prev = records[start_index - 1]
            max_odometer_end = prev.odometer_end or initial_odometer
            prev_fuel_remaining = prev.fuel_remaining if prev.fuel_remaining is not None else initial_fuel

            # MAX из всех G до start_index (на случай пропусков)
            for r in records[:start_index]:
                if r.odometer_end and r.odometer_end > max_odometer_end:
                    max_odometer_end = r.odometer_end

        for i in range(start_index, len(records)):
            rec = records[i]

            km_za_den = CalculationService.calculate_km_za_den(
                rec.odometer_end_day,
                rec.distance_km,
                max_odometer_end
            )

            # F: спидометр начало = MAX всех предыдущих G
            rec.odometer_start = max_odometer_end

            # E: бензин путевка
            rec.fuel_waybill = CalculationService.calculate_fuel_waybill(km_za_den, fuel_rate)

            # G: спидометр конец
            if km_za_den == 0 and not rec.odometer_end_day and not rec.distance_km:
                # Выходной: спидометр пустой (как в Excel: " ")
                rec.odometer_end = None
            else:
                rec.odometer_end = max_odometer_end + km_za_den

            # H: бензин остаток
            rec.fuel_remaining = CalculationService.calculate_fuel_remaining(
                prev_fuel_remaining,
                rec.fuel_waybill,
                rec.fuel_received,
                km_za_den
            )

            # Обновляем для следующей итерации
            if rec.odometer_end and rec.odometer_end > max_odometer_end:
                max_odometer_end = rec.odometer_end
            prev_fuel_remaining = rec.fuel_remaining

        return records
