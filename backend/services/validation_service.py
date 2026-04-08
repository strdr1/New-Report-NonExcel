class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class ValidationService:
    """Service for data validation"""
    
    @staticmethod
    def validate_profile(data):
        """Validate profile data - Property 16"""
        errors = []
        
        # Check required fields
        required_fields = ['name', 'car_brand', 'license_plate']
        for field in required_fields:
            if not data.get(field) or not str(data.get(field)).strip():
                errors.append({'field': field, 'message': f'{field} не может быть пустым'})
        
        if errors:
            return False, errors
        return True, None
    
    @staticmethod
    def validate_numeric_value(value, field_name):
        """Validate that numeric value is positive - Property 17"""
        try:
            num_value = float(value)
            if num_value < 0:
                return False, f'{field_name} должно быть положительным числом'
            return True, None
        except (ValueError, TypeError):
            return False, f'{field_name} должно быть числом'
    
    @staticmethod
    def validate_odometer(odometer_start, odometer_end):
        """Validate odometer consistency - Property 18"""
        if odometer_end < odometer_start:
            return False, 'Спидометр конца дня должен быть >= спидометра начала дня'
        return True, None
    
    @staticmethod
    def validate_distance(distance, odometer_start, odometer_end, tolerance=0.1):
        """Validate distance corresponds to odometer difference - Property 19"""
        calculated_distance = odometer_end - odometer_start
        if abs(distance - calculated_distance) > tolerance:
            return False, f'Расстояние ({distance}) не соответствует разнице спидометра ({calculated_distance})'
        return True, None
