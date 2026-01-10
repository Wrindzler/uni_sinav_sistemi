"""
DERSLİK MODELİ
==============
Üniversitedeki derslikleri temsil eder.

Her derslik bir sınav için kullanılabilir ve kapasitesi vardır.
"""

from models.database import db


class Derslik(db.Model):
    """
    Derslik tablosu.
    
    Üniversitedeki tüm derslikleri saklar.
    Her derslik sınav için kullanılabilir ve kapasitesi vardır.
    """
    
    __tablename__ = 'derslikler'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Derslik ID')
    
    # Derslik bilgileri
    ad = db.Column(db.String(100), unique=True, nullable=False,
                  comment='Derslik adı (örn: A-101)')
    kapasite = db.Column(db.Integer, nullable=False, default=30,
                        comment='Derslik kapasitesi (öğrenci sayısı)')
    
    # Sınav için uygunluk durumu
    sinav_icin_uygun = db.Column(db.Boolean, default=True, nullable=False,
                                 comment='Bu derslik sınav için uygun mu?')
    
    # Opsiyonel: Derslik yakın bilgisi
    bina = db.Column(db.String(100), nullable=True, comment='Bina adı')
    kat = db.Column(db.String(20), nullable=True, comment='Kat bilgisi')
    aciklama = db.Column(db.Text, nullable=True, comment='Derslik açıklaması')

    # Derslik yakınlıkları (JSON formatında saklanır)
    # Örnek: {"M101": ["S101", "M201", "M301", "S201", "S202"], "M201": ["M101", "S101", "S202"]}
    yakinliklar = db.Column(db.JSON, nullable=True, comment='Yakın derslikler listesi')
    
    # İlişkiler
    # Bir derslikte birden fazla sınav yapılabilir (farklı zamanlarda)
    sinavlar = db.relationship('Sinav', backref='derslik', lazy=True)
    
    def __repr__(self):
        """
        Derslik nesnesinin string temsili.
        
        Returns:
            str: Derslik adı ve kapasitesi
        """
        return f'<Derslik {self.ad} (Kapasite: {self.kapasite})>'

