"""
BÖLÜM YETKİLİSİ MODELİ
======================
Üniversitedeki bölüm yetkililerini temsil eder.

Her bölüm yetkilisi bir fakülte ve bölüme aittir.
Kendi bölümüne ait dersleri, öğretim üyelerini ve özel durumları sisteme girer.
"""

from models.database import db


class BolumYetkilisi(db.Model):
    """
    Bölüm yetkilisi tablosu.

    Üniversitedeki tüm bölüm yetkililerini saklar.
    """

    __tablename__ = 'bolum_yetkilileri'

    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Bölüm yetkilisi ID')

    # Bölüm yetkilisi bilgileri
    ad = db.Column(db.String(100), nullable=False, comment='Ad')
    soyad = db.Column(db.String(100), nullable=False, comment='Soyad')
    email = db.Column(db.String(120), unique=True, nullable=True,
                     comment='E-posta adresi')
    telefon = db.Column(db.String(20), nullable=True, comment='Telefon numarası')

    # Fakülte ve Bölüm bilgileri
    fakulte_id = db.Column(db.Integer, db.ForeignKey('fakulteler.id'),
                          nullable=False, comment='Bölüm yetkilisinin fakültesi')
    bolum_id = db.Column(db.Integer, db.ForeignKey('bolumler.id'),
                        nullable=False, comment='Bölüm yetkilisinin bölümü')

    # İlişkiler
    # Fakülte ve bölüm ilişkileri
    fakulte = db.relationship('Fakulte', backref='bolum_yetkilileri', lazy=True)
    bolum = db.relationship('Bolum', backref='bolum_yetkilileri', lazy=True)

    @property
    def tam_ad(self):
        """
        Bölüm yetkilisinin tam adını döndür.

        Returns:
            str: Ad + Soyad
        """
        return f'{self.ad} {self.soyad}'

    def __repr__(self):
        """
        Bölüm yetkilisi nesnesinin string temsili.

        Returns:
            str: Bölüm yetkilisinin tam adı
        """
        return f'<BolumYetkilisi {self.tam_ad}>'
