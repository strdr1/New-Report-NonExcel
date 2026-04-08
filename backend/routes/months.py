from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.models import Profile, Year, Month, DailyRecord
from backend.services.calculation_service import CalculationService

bp = Blueprint('months', __name__, url_prefix='/api/profiles')


def _get_initial_values(db, year, month_num):
    """Получить начальные значения спидометра и бензина для месяца."""
    if month_num == 1:
        return year.initial_odometer or 0.0, year.initial_fuel or 0.0

    prev_month = db.query(Month).filter(
        Month.year_id == year.id,
        Month.month == month_num - 1
    ).first()

    if prev_month:
        last = db.query(DailyRecord).filter(
            DailyRecord.month_id == prev_month.id
        ).order_by(DailyRecord.day.desc()).first()
        if last:
            return (last.odometer_end or 0.0), (last.fuel_remaining or 0.0)

    return 0.0, 0.0


def _fuel_rate(profile, month_num, month=None):
    """
    Норма расхода: сначала берётся из месяца (если задана вручную),
    затем из профиля по сезону, с fallback на другую норму.
    """
    if month and month.fuel_rate:
        return month.fuel_rate
    is_winter = month_num in (12, 1, 2)
    if is_winter:
        return profile.fuel_rate_winter or profile.fuel_rate_summer or 0.0
    else:
        return profile.fuel_rate_summer or profile.fuel_rate_winter or 0.0


@bp.route('/<int:profile_id>/years/<int:year_value>/months', methods=['GET'])
def get_months(profile_id, year_value):
    db = next(get_db())
    try:
        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден'}), 404
        months = db.query(Month).filter(Month.year_id == year.id).all()
        return jsonify([m.to_dict() for m in months]), 200
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>/months/<int:month_num>', methods=['GET'])
def get_month(profile_id, year_value, month_num):
    db = next(get_db())
    try:
        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден'}), 404

        month = db.query(Month).filter(Month.year_id == year.id, Month.month == month_num).first()
        if not month:
            return jsonify({'error': 'Not Found', 'message': f'Месяц {month_num} не найден'}), 404

        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        initial_odometer, initial_fuel = _get_initial_values(db, year, month_num)
        fuel_rate = _fuel_rate(profile, month_num, month)

        records = db.query(DailyRecord).filter(
            DailyRecord.month_id == month.id
        ).order_by(DailyRecord.day).all()

        result = month.to_dict()
        result['computed_initial_odometer'] = initial_odometer
        result['computed_initial_fuel'] = initial_fuel
        result['computed_fuel_rate'] = fuel_rate
        result['daily_records'] = [r.to_dict() for r in records]
        return jsonify(result), 200
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>/months/<int:month_num>/report', methods=['GET'])
def get_report(profile_id, year_value, month_num):
    """Отчёт: все дни месяца с расчётными значениями для второй таблицы."""
    db = next(get_db())
    try:
        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден'}), 404

        month = db.query(Month).filter(Month.year_id == year.id, Month.month == month_num).first()
        if not month:
            return jsonify({'error': 'Not Found', 'message': f'Месяц {month_num} не найден'}), 404

        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        initial_odometer, initial_fuel = _get_initial_values(db, year, month_num)
        fuel_rate = _fuel_rate(profile, month_num, month)

        records = db.query(DailyRecord).filter(
            DailyRecord.month_id == month.id
        ).order_by(DailyRecord.day).all()

        # Строим данные отчёта по тем же формулам, что и Excel
        report_rows = []
        max_odometer_end = initial_odometer
        prev_fuel_remaining = initial_fuel

        for rec in records:
            km_za_den = CalculationService.calculate_km_za_den(
                rec.odometer_end_day, rec.distance_km, max_odometer_end
            )

            # Начало дня (л): если это первый день с пробегом — K4, иначе H_предыдущего
            fuel_start = prev_fuel_remaining if km_za_den > 0 else None

            odometer_start = max_odometer_end if km_za_den > 0 else None
            odometer_end_report = (max_odometer_end + km_za_den) if km_za_den > 0 else None

            fuel_waybill = CalculationService.calculate_fuel_waybill(km_za_den, fuel_rate)
            fuel_remaining = CalculationService.calculate_fuel_remaining(
                prev_fuel_remaining, fuel_waybill, rec.fuel_received, km_za_den
            )
            fuel_end = fuel_remaining if km_za_den > 0 else None

            report_rows.append({
                'day': rec.day,
                'odometer_start': odometer_start,       # D: начало дня км
                'fuel_start': fuel_start,               # E: начало дня л
                'odometer_end': odometer_end_report,    # F: конец дня км
                'fuel_end': fuel_end,                   # G: конец дня л
                'fuel_received': rec.fuel_received,     # H: получено бензина
                'km_za_den': km_za_den if km_za_den > 0 else None,  # I: за день км
                'fuel_waybill': fuel_waybill if km_za_den > 0 else None,  # J: за день л
            })

            if odometer_end_report and odometer_end_report > max_odometer_end:
                max_odometer_end = odometer_end_report
            if km_za_den > 0:
                prev_fuel_remaining = fuel_remaining

        return jsonify(report_rows), 200
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>/months/<int:month_num>', methods=['PUT'])
def update_month(profile_id, year_value, month_num):
    """Обновить настройки месяца (норма расхода) и пересчитать все дни."""
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': 'Профиль не найден'}), 404

        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден'}), 404

        month = db.query(Month).filter(Month.year_id == year.id, Month.month == month_num).first()
        if not month:
            return jsonify({'error': 'Not Found', 'message': f'Месяц {month_num} не найден'}), 404

        data = request.get_json()
        if 'fuel_rate' in data:
            val = data['fuel_rate']
            month.fuel_rate = float(val) if val not in (None, '', 0) else None

        # Пересчитываем все дни с новой нормой
        all_records = db.query(DailyRecord).filter(
            DailyRecord.month_id == month.id
        ).order_by(DailyRecord.day).all()

        initial_odometer, initial_fuel = _get_initial_values(db, year, month_num)
        fuel_rate = _fuel_rate(profile, month_num, month)
        CalculationService.recalculate_from(all_records, 0, initial_odometer, initial_fuel, fuel_rate)

        db.commit()
        return jsonify(month.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>/months/<int:month_num>/days/<int:day_num>', methods=['PUT'])
def update_daily_record(profile_id, year_value, month_num, day_num):
    """Обновить запись дня и пересчитать все зависимые значения."""
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': 'Профиль не найден'}), 404

        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден'}), 404

        month = db.query(Month).filter(Month.year_id == year.id, Month.month == month_num).first()
        if not month:
            return jsonify({'error': 'Not Found', 'message': f'Месяц {month_num} не найден'}), 404

        record = db.query(DailyRecord).filter(
            DailyRecord.month_id == month.id,
            DailyRecord.day == day_num
        ).first()
        if not record:
            return jsonify({'error': 'Not Found', 'message': f'День {day_num} не найден'}), 404

        data = request.get_json()

        # Обновляем только вводимые поля (C, D, I)
        if 'odometer_end_day' in data:
            val = data['odometer_end_day']
            record.odometer_end_day = float(val) if val not in (None, '', 0) else None
        if 'distance_km' in data:
            val = data['distance_km']
            record.distance_km = float(val) if val not in (None, '', 0) else None
        if 'fuel_received' in data:
            val = data['fuel_received']
            record.fuel_received = float(val) if val not in (None, '', 0) else None

        # Собираем все записи месяца
        all_records = db.query(DailyRecord).filter(
            DailyRecord.month_id == month.id
        ).order_by(DailyRecord.day).all()

        initial_odometer, initial_fuel = _get_initial_values(db, year, month_num)
        fuel_rate = _fuel_rate(profile, month_num, month)

        # Пересчитываем начиная с изменённого дня
        start_index = next((i for i, r in enumerate(all_records) if r.day == day_num), 0)
        CalculationService.recalculate_from(all_records, start_index, initial_odometer, initial_fuel, fuel_rate)

        db.commit()
        return jsonify(record.to_dict()), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()
