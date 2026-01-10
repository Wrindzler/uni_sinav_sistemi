"""
ROUTE MODÜLLERİ
===============
Flask route'larını organize eder.

Her route modülü farklı bir işlevsellik alanını kapsar.
"""

from routes.auth import auth_bp
from routes.ders import ders_bp
from routes.derslik import derslik_bp
from routes.sinav import sinav_bp
from routes.planlama import planlama_bp
from routes.rapor import rapor_bp
from routes.admin import admin_bp
from routes.ogrenci import ogrenci_bp
from routes.ozel_durum import ozel_durum_bp

__all__ = [
    'auth_bp',
    'ders_bp',
    'derslik_bp',
    'sinav_bp',
    'planlama_bp',
    'rapor_bp',
    'admin_bp',
    'ogrenci_bp',
    'ozel_durum_bp'
]

