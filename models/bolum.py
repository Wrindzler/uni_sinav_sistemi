"""
BÖLÜM MODELİ
============
Fakültelere ait bölümleri temsil eder.

Her bölüm bir fakülteye aittir ve birden fazla dersi olabilir.
"""

from models.database import db


class Bolum(db.Model):
    """
    Bölüm tablosu.
    
    Fakültelere ait bölümleri saklar.
    Örnek: Bilgisayar Mühendisliği, Elektrik Mühendisliği
    """
    
    __tablename__ = 'bolumler'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Bölüm ID')
    
    # Bölüm bilgileri
    ad = db.Column(db.String(200), nullable=False, comment='Bölüm adı')
    kod = db.Column(db.String(20), nullable=True, comment='Bölüm kodu')
    aciklama = db.Column(db.Text, nullable=True, comment='Bölüm açıklaması')
    
    # İlişkiler
    # Her bölüm bir fakülteye aittir
    fakulte_id = db.Column(db.Integer, db.ForeignKey('fakulteler.id'),
                          nullable=False, index=True, comment='Bağlı olduğu fakülte ID')
    
    # Bir bölümün birden fazla dersi olabilir
    dersler = db.relationship('Ders', backref='bolum', lazy=True,
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        """
        Bölüm nesnesinin string temsili.
        
        Returns:
            str: Bölüm adı
        """
        return f'<Bolum {self.ad}>'

