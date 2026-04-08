from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.models import Profile, Year, Month, DailyRecord

bp = Blueprint('years', __name__, url_prefix='/api/profiles')

@bp.route('/<int:profile_id>/years', methods=['GET'])
def get_years(profile_id):
    """Get all years for a profile"""
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': f'Профиль с ID {profile_id} не найден'}), 404
        
        years = db.query(Year).filter(Year.profile_id == profile_id).all()
        return jsonify([year.to_dict() for year in years]), 200
    finally:
        db.close()


@bp.route('/<int:profile_id>/years', methods=['POST'])
def create_year(profile_id):
    """Create a new year with 12 months and daily records"""
    data = request.get_json()
    year_value = data.get('year')
    
    if not year_value:
        return jsonify({'error': 'Validation Error', 'details': [{'field': 'year', 'message': 'Год обязателен'}]}), 400
    
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': f'Профиль с ID {profile_id} не найден'}), 404
        
        # Check if year already exists
        existing_year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if existing_year:
            return jsonify({'error': 'Conflict', 'message': f'Год {year_value} уже добавлен к этому профилю'}), 409
        
        # Determine if leap year
        is_leap = Year.is_leap(year_value)
        
        # Create year
        year = Year(profile_id=profile_id, year=year_value, is_leap_year=is_leap)
        db.add(year)
        db.flush()
        
        # Create 12 months with daily records
        for month_num in range(1, 13):
            days_in_month = Month.get_days_in_month(month_num, is_leap)
            month = Month(year_id=year.id, month=month_num, days_in_month=days_in_month)
            db.add(month)
            db.flush()
            
            # Create daily records for each day
            for day_num in range(1, days_in_month + 1):
                daily_record = DailyRecord(month_id=month.id, day=day_num)
                db.add(daily_record)
        
        db.commit()
        db.refresh(year)
        return jsonify(year.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>', methods=['GET'])
def get_year(profile_id, year_value):
    """Get year with months information"""
    db = next(get_db())
    try:
        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден для профиля {profile_id}'}), 404
        
        # Get months with data status
        months = db.query(Month).filter(Month.year_id == year.id).all()
        months_data = []
        for month in months:
            # Check if month has any data
            has_data = db.query(DailyRecord).filter(
                DailyRecord.month_id == month.id,
                (DailyRecord.distance_km != None) | (DailyRecord.odometer_end_day != None)
            ).first() is not None
            
            months_data.append({
                'month': month.month,
                'days_in_month': month.days_in_month,
                'has_data': has_data
            })
        
        result = year.to_dict()
        result['months'] = months_data
        return jsonify(result), 200
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>', methods=['PUT'])
def update_year(profile_id, year_value):
    """Update year initial values"""
    db = next(get_db())
    try:
        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден для профиля {profile_id}'}), 404
        
        data = request.get_json()
        
        if 'initial_odometer' in data:
            year.initial_odometer = float(data['initial_odometer'])
        if 'initial_fuel' in data:
            year.initial_fuel = float(data['initial_fuel'])
        
        db.commit()
        db.refresh(year)
        return jsonify(year.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()


@bp.route('/<int:profile_id>/years/<int:year_value>', methods=['DELETE'])
def delete_year(profile_id, year_value):
    """Delete year (cascade delete months and daily records)"""
    db = next(get_db())
    try:
        year = db.query(Year).filter(Year.profile_id == profile_id, Year.year == year_value).first()
        if not year:
            return jsonify({'error': 'Not Found', 'message': f'Год {year_value} не найден для профиля {profile_id}'}), 404
        
        db.delete(year)
        db.commit()
        return jsonify({'message': 'Год успешно удалён'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()
