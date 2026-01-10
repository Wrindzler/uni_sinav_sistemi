"""
KULLANICI MODELİ
================
Sistem kullanıcılarını temsil eder.

Kullanıcı rolleri:
- admin: Tüm sistemi yönetir
- bolum_yetkilisi: Kendi bölümünü yönetir
- hoca: Sadece görüntüleme
- ogrenci: Sadece görüntüleme (opsiyonel)
"""

from models.database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    """
    Kullanıcı tablosu.
    
    Flask-Login ile entegre çalışır.
    Şifreler hash'lenerek saklanır (güvenlik için).
    """
    
    __tablename__ = 'users'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, comment='Kullanıcı ID')
    
    # Kullanıcı bilgileri
    kullanici_adi = db.Column(db.String(80), unique=True, nullable=False, 
                              comment='Kullanıcı adı (benzersiz)')
    email = db.Column(db.String(120), unique=True, nullable=False,
                     comment='E-posta adresi')
    sifre_hash = db.Column(db.String(255), nullable=False,
                           comment='Hash\'lenmiş şifre')
    
    # Rol bilgisi (admin, bolum_yetkilisi, hoca, ogrenci)
    rol = db.Column(db.String(50), nullable=False, default='ogrenci',
                   comment='Kullanıcı rolü')
    
    # İlişkiler
    # Eğer kullanıcı bir öğretim üyesi ise, bu alan dolu olur
    ogretim_uyesi_id = db.Column(db.Integer, db.ForeignKey('ogretim_uyeleri.id'),
                                 nullable=True, comment='Öğretim üyesi ID (eğer hoca ise)')

    # Eğer kullanıcı bir öğrenci ise, bu alan dolu olur
    ogrenci_id = db.Column(db.Integer, db.ForeignKey('ogrenciler.id'),
                          nullable=True, comment='Öğrenci ID (eğer öğrenci ise)')

    # Eğer kullanıcı bölüm yetkilisi ise, bu alan dolu olur
    bolum_yetkilisi_id = db.Column(db.Integer, db.ForeignKey('bolum_yetkilileri.id'),
                                   nullable=True, comment='Bölüm yetkilisi ID (eğer bölüm yetkilisi ise)')

    # Eski bölüm ID alanı (geriye dönük uyumluluk için - artık kullanılmıyor)
    bolum_id = db.Column(db.Integer, db.ForeignKey('bolumler.id'),
                        nullable=True, comment='Bölüm ID (eski alan)')
    
    # Zaman damgaları
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow,
                                 comment='Hesap oluşturulma tarihi')
    son_giris = db.Column(db.DateTime, nullable=True,
                         comment='Son giriş tarihi')
    
    # Aktiflik durumu
    aktif = db.Column(db.Boolean, default=True, nullable=False,
                     comment='Hesap aktif mi?')
    
    def __init__(self, kullanici_adi, email, sifre, rol='ogrenci'):
        """
        Yeni kullanıcı oluştur.
        
        Args:
            kullanici_adi: Kullanıcı adı
            email: E-posta adresi
            sifre: Şifre (hash'lenecek)
            rol: Kullanıcı rolü
        """
        self.kullanici_adi = kullanici_adi
        self.email = email
        self.set_password(sifre)  # Şifreyi hash'le
        self.rol = rol
    
    def set_password(self, sifre):
        """
        Şifreyi hash'le ve kaydet.
        
        Güvenlik için şifreler düz metin olarak saklanmaz.
        Werkzeug'un generate_password_hash fonksiyonu kullanılır.
        
        Args:
            sifre: Düz metin şifre
        """
        self.sifre_hash = generate_password_hash(sifre)
    
    def check_password(self, sifre):
        """
        Şifrenin doğru olup olmadığını kontrol et.
        
        Args:
            sifre: Kontrol edilecek şifre
            
        Returns:
            bool: Şifre doğruysa True
        """
        return check_password_hash(self.sifre_hash, sifre)
    
    def is_admin(self):
        """
        Kullanıcının admin olup olmadığını kontrol et.
        
        Returns:
            bool: Admin ise True
        """
        return self.rol == 'admin'
    
    def is_bolum_yetkilisi(self):
        """
        Kullanıcının bölüm yetkilisi olup olmadığını kontrol et.
        
        Returns:
            bool: Bölüm yetkilisi ise True
        """
        return self.rol == 'bolum_yetkilisi'
    
    def is_hoca(self):
        """
        Kullanıcının hoca olup olmadığını kontrol et.
        
        Returns:
            bool: Hoca ise True
        """
        return self.rol == 'hoca'
    
    def is_ogrenci(self):
        """
        Kullanıcının öğrenci olup olmadığını kontrol et.
        
        Returns:
            bool: Öğrenci ise True
        """
        return self.rol == 'ogrenci'
    
    def __repr__(self):
        """
        Kullanıcı nesnesinin string temsili.
        
        Returns:
            str: Kullanıcı adı ve rolü
        """
        return f'<User {self.kullanici_adi} ({self.rol})>'

