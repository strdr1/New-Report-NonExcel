from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    car_brand = Column(String, nullable=False)
    license_plate = Column(String, nullable=False)
    accounting = Column(String, nullable=True)
    fuel_rate_summer = Column(Float, nullable=True)  # Норма расхода летом (л/100км)
    fuel_rate_winter = Column(Float, nullable=True)  # Норма расхода зимой (л/100км)
    fuel_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    years = relationship("Year", back_populates="profile", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'car_brand': self.car_brand,
            'license_plate': self.license_plate,
            'accounting': self.accounting,
            'fuel_rate_summer': self.fuel_rate_summer,
            'fuel_rate_winter': self.fuel_rate_winter,
            'fuel_type': self.fuel_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Year(Base):
    __tablename__ = 'years'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)
    is_leap_year = Column(Boolean, nullable=False)
    initial_odometer = Column(Float, default=0.0)  # Спидометр на конец предыдущего года (E4 первого месяца)
    initial_fuel = Column(Float, default=0.0)       # Остаток бензина на конец предыдущего года (K4 первого месяца)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="years")
    months = relationship("Month", back_populates="year", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'year': self.year,
            'is_leap_year': self.is_leap_year,
            'initial_odometer': self.initial_odometer,
            'initial_fuel': self.initial_fuel,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def is_leap(year):
        if year % 400 == 0:
            return True
        if year % 100 == 0:
            return False
        if year % 4 == 0:
            return True
        return False


class Month(Base):
    __tablename__ = 'months'

    id = Column(Integer, primary_key=True, autoincrement=True)
    year_id = Column(Integer, ForeignKey('years.id', ondelete='CASCADE'), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    days_in_month = Column(Integer, nullable=False)
    initial_odometer = Column(Float, default=0.0)  # E4: спидометр на конец предыдущего месяца
    initial_fuel = Column(Float, default=0.0)       # K4: остаток бензина на конец предыдущего месяца
    fuel_rate = Column(Float, nullable=True)         # P4: норма расхода для этого месяца (переопределяет профиль)
    created_at = Column(DateTime, default=datetime.utcnow)

    year = relationship("Year", back_populates="months")
    daily_records = relationship("DailyRecord", back_populates="month", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'year_id': self.year_id,
            'month': self.month,
            'days_in_month': self.days_in_month,
            'initial_odometer': self.initial_odometer,
            'initial_fuel': self.initial_fuel,
            'fuel_rate': self.fuel_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def get_days_in_month(month, is_leap_year):
        days_map = {
            1: 31, 2: 29 if is_leap_year else 28, 3: 31, 4: 30,
            5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        return days_map.get(month, 30)


class DailyRecord(Base):
    __tablename__ = 'daily_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    month_id = Column(Integer, ForeignKey('months.id', ondelete='CASCADE'), nullable=False)
    day = Column(Integer, nullable=False)  # 1-31

    # Колонка C: Спидометр конец дня (ввод, используется когда нет путевки)
    odometer_end_day = Column(Float, nullable=True)

    # Колонка D: Пробег путевка (ввод)
    distance_km = Column(Float, nullable=True)

    # Колонка I: Бензин получено (ввод)
    fuel_received = Column(Float, nullable=True)

    # Колонка E: Бензин путевка (расчёт: km_za_den * норма / 100)
    fuel_waybill = Column(Float, nullable=True)

    # Колонка F: Спидометр начало (расчёт: MAX всех предыдущих G)
    odometer_start = Column(Float, nullable=True)

    # Колонка G: Спидометр конец (расчёт: F + km_za_den)
    odometer_end = Column(Float, nullable=True)

    # Колонка H: Бензин остаток (расчёт)
    fuel_remaining = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    month = relationship("Month", back_populates="daily_records")

    def to_dict(self):
        return {
            'id': self.id,
            'month_id': self.month_id,
            'day': self.day,
            'odometer_end_day': self.odometer_end_day,   # C
            'distance_km': self.distance_km,              # D
            'fuel_waybill': self.fuel_waybill,            # E
            'odometer_start': self.odometer_start,        # F
            'odometer_end': self.odometer_end,            # G
            'fuel_remaining': self.fuel_remaining,        # H
            'fuel_received': self.fuel_received,          # I
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
