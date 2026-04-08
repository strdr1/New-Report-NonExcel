from flask import Blueprint, request, jsonify
from backend.database import get_db
from backend.models import Profile
from backend.services.validation_service import ValidationService

bp = Blueprint('profiles', __name__, url_prefix='/api/profiles')

@bp.route('', methods=['GET'])
def get_profiles():
    """Get all profiles"""
    db = next(get_db())
    try:
        profiles = db.query(Profile).all()
        return jsonify([profile.to_dict() for profile in profiles]), 200
    finally:
        db.close()


@bp.route('', methods=['POST'])
def create_profile():
    """Create a new profile"""
    data = request.get_json()
    
    # Validate profile data
    is_valid, errors = ValidationService.validate_profile(data)
    if not is_valid:
        return jsonify({'error': 'Validation Error', 'details': errors}), 400
    
    db = next(get_db())
    try:
        def _float(val):
            try: return float(val) if val not in (None, '', '0', 0) else None
            except: return None

        profile = Profile(
            name=data['name'],
            car_brand=data['car_brand'],
            license_plate=data['license_plate'],
            accounting=data.get('accounting'),
            fuel_rate_summer=_float(data.get('fuel_rate_summer')),
            fuel_rate_winter=_float(data.get('fuel_rate_winter')),
            fuel_type=data.get('fuel_type') or None,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return jsonify(profile.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()


@bp.route('/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Get profile by ID"""
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': f'Профиль с ID {profile_id} не найден'}), 404
        return jsonify(profile.to_dict()), 200
    finally:
        db.close()


@bp.route('/<int:profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update profile"""
    data = request.get_json()
    
    # Validate profile data
    is_valid, errors = ValidationService.validate_profile(data)
    if not is_valid:
        return jsonify({'error': 'Validation Error', 'details': errors}), 400
    
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': f'Профиль с ID {profile_id} не найден'}), 404
        
        def _float(val):
            try: return float(val) if val not in (None, '', '0', 0) else None
            except: return None

        profile.name = data['name']
        profile.car_brand = data['car_brand']
        profile.license_plate = data['license_plate']
        profile.accounting = data.get('accounting')
        profile.fuel_rate_summer = _float(data.get('fuel_rate_summer'))
        profile.fuel_rate_winter = _float(data.get('fuel_rate_winter'))
        profile.fuel_type = data.get('fuel_type') or None
        
        db.commit()
        db.refresh(profile)
        return jsonify(profile.to_dict()), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()


@bp.route('/<int:profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    """Delete profile (cascade delete years, months, daily records)"""
    db = next(get_db())
    try:
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            return jsonify({'error': 'Not Found', 'message': f'Профиль с ID {profile_id} не найден'}), 404
        
        db.delete(profile)
        db.commit()
        return jsonify({'message': 'Профиль успешно удалён'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    finally:
        db.close()
