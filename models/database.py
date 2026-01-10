"""
VERİTABANI BAĞLANTISI
=====================
SQLAlchemy veritabanı bağlantısını yönetir.

Bu modül, tüm modellerin kullanacağı ortak veritabanı
bağlantı nesnesini sağlar.
"""

from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy veritabanı nesnesi
# Bu nesne tüm modeller tarafından kullanılacak
db = SQLAlchemy()

