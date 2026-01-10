"""
VERİTABANI GÖRÜNTÜLEME ARACI
============================
Veritabanındaki tüm tabloları ve içeriklerini görüntüler.

Bu script, veritabanındaki tüm verileri düzenli bir şekilde
konsola yazdırır. Veritabanı içeriğini kontrol etmek ve
debug yapmak için kullanışlıdır.
"""

import sys
from pathlib import Path

# Proje dizinini Python path'ine ekle
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from flask import Flask
from config import Config
from models import (
    db, User, Fakulte, Bolum, Ders, OgretimUyesi, 
    Derslik, Sinav, Ogrenci, OgrenciDers, OzelDurum
)
from models.bolum_yetkilisi import BolumYetkilisi


def print_separator(title="", width=80):
    """Başlık ile ayırıcı çizgi yazdır."""
    if title:
        print("\n" + "=" * width)
        print(f" {title}")
        print("=" * width)
    else:
        print("-" * width)


def print_table_header(columns):
    """Tablo başlığını yazdır."""
    header = " | ".join(str(col).ljust(15) for col in columns)
    print(header)
    print("-" * len(header))


def format_value(value, max_length=15):
    """Değeri formatlayıp kırp."""
    if value is None:
        return "NULL".ljust(max_length)
    
    value_str = str(value)
    if len(value_str) > max_length:
        return value_str[:max_length-3] + "..."
    return value_str.ljust(max_length)


def print_users():
    """Kullanıcıları görüntüle."""
    print_separator("KULLANICILAR (Users)")
    users = User.query.all()
    
    if not users:
        print("❌ Hiç kullanıcı bulunamadı.")
        return
    
    print(f"📊 Toplam {len(users)} kullanıcı bulundu.\n")
    print_table_header(["ID", "Kullanıcı Adı", "Email", "Rol", "Aktif"])
    
    for user in users:
        print(
            f"{format_value(user.id)} | "
            f"{format_value(user.kullanici_adi)} | "
            f"{format_value(user.email)} | "
            f"{format_value(user.rol)} | "
            f"{format_value(user.aktif)}"
        )


def print_fakulteler():
    """Fakülteleri görüntüle."""
    print_separator("FAKÜLTELER (Fakulteler)")
    fakulteler = Fakulte.query.all()
    
    if not fakulteler:
        print("❌ Hiç fakülte bulunamadı.")
        return
    
    print(f"📊 Toplam {len(fakulteler)} fakülte bulundu.\n")
    print_table_header(["ID", "Ad", "Kod", "Bölüm Sayısı"])
    
    for fakulte in fakulteler:
        print(
            f"{format_value(fakulte.id)} | "
            f"{format_value(fakulte.ad, 30)} | "
            f"{format_value(fakulte.kod)} | "
            f"{format_value(len(fakulte.bolumler))}"
        )


def print_bolumler():
    """Bölümleri görüntüle."""
    print_separator("BÖLÜMLER (Bolumler)")
    bolumler = Bolum.query.all()
    
    if not bolumler:
        print("❌ Hiç bölüm bulunamadı.")
        return
    
    print(f"📊 Toplam {len(bolumler)} bölüm bulundu.\n")
    print_table_header(["ID", "Ad", "Kod", "Fakülte", "Ders Sayısı"])
    
    for bolum in bolumler:
        fakulte_ad = bolum.fakulte.ad if bolum.fakulte else "Yok"
        print(
            f"{format_value(bolum.id)} | "
            f"{format_value(bolum.ad, 25)} | "
            f"{format_value(bolum.kod)} | "
            f"{format_value(fakulte_ad, 20)} | "
            f"{format_value(len(bolum.dersler))}"
        )


def print_bolum_yetkilileri():
    """Bölüm yetkililerini görüntüle."""
    print_separator("BÖLÜM YETKİLİLERİ (BolumYetkilileri)")
    yetkililer = BolumYetkilisi.query.all()
    
    if not yetkililer:
        print("❌ Hiç bölüm yetkilisi bulunamadı.")
        return
    
    print(f"📊 Toplam {len(yetkililer)} bölüm yetkilisi bulundu.\n")
    print_table_header(["ID", "Ad Soyad", "Email", "Bölüm"])
    
    for yetkili in yetkililer:
        bolum_ad = yetkili.bolum.ad if yetkili.bolum else "Yok"
        print(
            f"{format_value(yetkili.id)} | "
            f"{format_value(yetkili.tam_ad, 25)} | "
            f"{format_value(yetkili.email, 25)} | "
            f"{format_value(bolum_ad, 25)}"
        )


def print_ogretim_uyeleri():
    """Öğretim üyelerini görüntüle."""
    print_separator("ÖĞRETİM ÜYELERİ (OgretimUyeleri)")
    ogretim_uyeleri = OgretimUyesi.query.all()
    
    if not ogretim_uyeleri:
        print("❌ Hiç öğretim üyesi bulunamadı.")
        return
    
    print(f"📊 Toplam {len(ogretim_uyeleri)} öğretim üyesi bulundu.\n")
    print_table_header(["ID", "Ad Soyad", "Email", "Bölüm"])
    
    for ogretim_uyesi in ogretim_uyeleri:
        bolum_ad = ogretim_uyesi.bolum.ad if ogretim_uyesi.bolum else "Yok"
        print(
            f"{format_value(ogretim_uyesi.id)} | "
            f"{format_value(ogretim_uyesi.tam_ad, 25)} | "
            f"{format_value(ogretim_uyesi.email, 25)} | "
            f"{format_value(bolum_ad, 20)}"
        )


def print_dersler():
    """Dersleri görüntüle."""
    print_separator("DERSLER (Dersler)")
    dersler = Ders.query.all()
    
    if not dersler:
        print("❌ Hiç ders bulunamadı.")
        return
    
    print(f"📊 Toplam {len(dersler)} ders bulundu.\n")
    print_table_header(["ID", "Kod", "Ad", "Öğrenci", "Bölüm", "Hoca"])
    
    for ders in dersler:
        bolum_ad = ders.bolum.ad if ders.bolum else "Yok"
        hoca_ad = ders.ogretim_uyesi.tam_ad if ders.ogretim_uyesi else "Yok"
        print(
            f"{format_value(ders.id)} | "
            f"{format_value(ders.kod)} | "
            f"{format_value(ders.ad, 25)} | "
            f"{format_value(ders.ogrenci_sayisi)} | "
            f"{format_value(bolum_ad, 20)} | "
            f"{format_value(hoca_ad, 20)}"
        )


def print_ogrenciler():
    """Öğrencileri görüntüle."""
    print_separator("ÖĞRENCİLER (Ogrenciler)")
    ogrenciler = Ogrenci.query.all()
    
    if not ogrenciler:
        print("❌ Hiç öğrenci bulunamadı.")
        return
    
    print(f"📊 Toplam {len(ogrenciler)} öğrenci bulundu.\n")
    print_table_header(["ID", "No", "Ad Soyad", "Email", "Bölüm"])
    
    for ogrenci in ogrenciler:
        bolum_ad = ogrenci.bolum.ad if ogrenci.bolum else "Yok"
        print(
            f"{format_value(ogrenci.id)} | "
            f"{format_value(ogrenci.ogrenci_no)} | "
            f"{format_value(ogrenci.tam_ad, 25)} | "
            f"{format_value(ogrenci.email, 25)} | "
            f"{format_value(bolum_ad, 20)}"
        )


def print_ogrenci_dersler():
    """Öğrenci ders kayıtlarını görüntüle."""
    print_separator("ÖĞRENCİ DERS KAYITLARI (OgrenciDers)")
    ogrenci_dersler = OgrenciDers.query.all()
    
    if not ogrenci_dersler:
        print("❌ Hiç öğrenci ders kaydı bulunamadı.")
        return
    
    print(f"📊 Toplam {len(ogrenci_dersler)} öğrenci ders kaydı bulundu.\n")
    print_table_header(["ID", "Öğrenci No", "Öğrenci Adı", "Ders"])
    
    for kayit in ogrenci_dersler:
        ogrenci_no = kayit.ogrenci.ogrenci_no if kayit.ogrenci else "Yok"
        ogrenci_ad = kayit.ogrenci.tam_ad if kayit.ogrenci else "Yok"
        ders_ad = kayit.ders.ad if kayit.ders else "Yok"
        print(
            f"{format_value(kayit.id)} | "
            f"{format_value(ogrenci_no)} | "
            f"{format_value(ogrenci_ad, 25)} | "
            f"{format_value(ders_ad, 30)}"
        )


def print_derslikler():
    """Derslikleri görüntüle."""
    print_separator("DERSLİKLER (Derslikler)")
    derslikler = Derslik.query.all()
    
    if not derslikler:
        print("❌ Hiç derslik bulunamadı.")
        return
    
    print(f"📊 Toplam {len(derslikler)} derslik bulundu.\n")
    print_table_header(["ID", "Ad", "Kapasite", "Bina", "Kat"])
    
    for derslik in derslikler:
        print(
            f"{format_value(derslik.id)} | "
            f"{format_value(derslik.ad)} | "
            f"{format_value(derslik.kapasite)} | "
            f"{format_value(derslik.bina)} | "
            f"{format_value(derslik.kat)}"
        )


def print_sinavlar():
    """Sınavları görüntüle."""
    print_separator("SINAVLAR (Sinavlar)")
    sinavlar = Sinav.query.all()
    
    if not sinavlar:
        print("❌ Hiç sınav bulunamadı.")
        return
    
    print(f"📊 Toplam {len(sinavlar)} sınav bulundu.\n")
    print_table_header(["ID", "Ders", "Tarih", "Başlangıç", "Bitiş", "Derslik"])
    
    for sinav in sinavlar:
        ders_ad = sinav.ders.ad if sinav.ders else "Yok"
        derslik_ad = sinav.derslik.ad if sinav.derslik else "Atanmadı"
        tarih = sinav.tarih.strftime("%d.%m.%Y") if sinav.tarih else "Yok"
        baslangic = sinav.baslangic_saati.strftime("%H:%M") if sinav.baslangic_saati else "Yok"
        bitis = sinav.bitis_saati.strftime("%H:%M") if sinav.bitis_saati else "Yok"
        
        print(
            f"{format_value(sinav.id)} | "
            f"{format_value(ders_ad, 25)} | "
            f"{format_value(tarih)} | "
            f"{format_value(baslangic)} | "
            f"{format_value(bitis)} | "
            f"{format_value(derslik_ad, 15)}"
        )


def print_ozel_durumlar():
    """Özel durumları görüntüle."""
    print_separator("ÖZEL DURUMLAR (OzelDurumlar)")
    ozel_durumlar = OzelDurum.query.all()
    
    if not ozel_durumlar:
        print("❌ Hiç özel durum bulunamadı.")
        return
    
    print(f"📊 Toplam {len(ozel_durumlar)} özel durum bulundu.\n")
    print_table_header(["ID", "Durum Türü", "Ders/Hoca", "Açıklama"])
    
    for durum in ozel_durumlar:
        hedef = ""
        if durum.ders_id:
            hedef = f"Ders:{durum.ders_id}"
        elif durum.ogretim_uyesi_id:
            hedef = f"Hoca:{durum.ogretim_uyesi_id}"
        else:
            hedef = "Genel"
            
        aciklama_kisaltilmis = (durum.aciklama[:40] + "...") if durum.aciklama and len(durum.aciklama) > 40 else (durum.aciklama or "")
        print(
            f"{format_value(durum.id)} | "
            f"{format_value(durum.durum_turu, 20)} | "
            f"{format_value(hedef, 15)} | "
            f"{format_value(aciklama_kisaltilmis, 40)}"
        )


def print_istatistikler():
    """Genel istatistikleri görüntüle."""
    print_separator("GENEL İSTATİSTİKLER")
    
    stats = {
        "Kullanıcılar": User.query.count(),
        "Fakülteler": Fakulte.query.count(),
        "Bölümler": Bolum.query.count(),
        "Bölüm Yetkilileri": BolumYetkilisi.query.count(),
        "Öğretim Üyeleri": OgretimUyesi.query.count(),
        "Dersler": Ders.query.count(),
        "Öğrenciler": Ogrenci.query.count(),
        "Öğrenci Ders Kayıtları": OgrenciDers.query.count(),
        "Derslikler": Derslik.query.count(),
        "Sınavlar": Sinav.query.count(),
        "Özel Durumlar": OzelDurum.query.count(),
    }
    
    print()
    for key, value in stats.items():
        print(f"  📌 {key.ljust(30)}: {value}")


def main():
    """Ana fonksiyon - tüm veritabanını görüntüle."""
    # Flask uygulaması oluştur
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Veritabanını başlat
    db.init_app(app)
    
    # Uygulama bağlamında çalıştır
    with app.app_context():
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " VERİTABANI GÖRÜNTÜLEME ARACI ".center(78) + "║")
        print("╚" + "═" * 78 + "╝")
        
        # İstatistikleri göster
        print_istatistikler()
        
        # Tüm tabloları göster
        print_separator()
        print_users()
        print_fakulteler()
        print_bolumler()
        print_bolum_yetkilileri()
        print_ogretim_uyeleri()
        print_dersler()
        print_ogrenciler()
        print_ogrenci_dersler()
        print_derslikler()
        print_sinavlar()
        print_ozel_durumlar()
        
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " GÖRÜNTÜLEME TAMAMLANDI ".center(78) + "║")
        print("╚" + "═" * 78 + "╝")
        print("\n")


if __name__ == '__main__':
    main()

