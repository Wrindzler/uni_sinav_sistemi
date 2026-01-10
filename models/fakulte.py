"""
FAKÜLTE MODELİ
==============
Üniversitedeki fakülteleri temsil eder.

Her fakültenin birden fazla bölümü olabilir.
"""

from models.database import db


class Fakulte(db.Model):
    """
    Fakülte tablosu.
    
    Üniversitedeki fakülteleri saklar.
    Örnek: Mühendislik Fakültesi, Tıp Fakültesi
    """
    
    __tablename__ = 'fakulteler'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Fakülte ID')
    
    # Fakülte bilgileri
    ad = db.Column(db.String(200), unique=True, nullable=False,
                  comment='Fakülte adı')
    kod = db.Column(db.String(20), unique=True, nullable=True,
                   comment='Fakülte kodu (opsiyonel)')
    aciklama = db.Column(db.Text, nullable=True,
                        comment='Fakülte açıklaması')
    
    # İlişkiler
    # Bir fakültenin birden fazla bölümü olabilir
    bolumler = db.relationship('Bolum', backref='fakulte', lazy=True,
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        """
        Fakülte nesnesinin string temsili.
        
        Returns:
            str: Fakülte adı
        """
        return f'<Fakulte {self.ad}>'

