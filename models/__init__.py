"""
VERİTABANI MODELLERİ
====================
Tüm veritabanı modelleri bu pakette tanımlanır.

Bu modül, SQLAlchemy ORM kullanarak veritabanı tablolarını
Python sınıfları olarak tanımlar.
"""

from models.database import db
from models.user import User
from models.fakulte import Fakulte
from models.bolum import Bolum
from models.ders import Ders, ders_bolumler
from models.ogretim_uyesi import OgretimUyesi
from models.derslik import Derslik
from models.sinav import Sinav
from models.ogrenci import Ogrenci
from models.ogrenci_ders import OgrenciDers
from models.ozel_durum import OzelDurum

__all__ = [
    'db',
    'User',
    'Fakulte',
    'Bolum',
    'Ders',
    'ders_bolumler',
    'OgretimUyesi',
    'Derslik',
    'Sinav',
    'Ogrenci',
    'OgrenciDers',
    'OzelDurum'
]

