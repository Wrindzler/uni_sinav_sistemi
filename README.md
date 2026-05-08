# Uni Sinav Sistemi

Universite sinav programlarinin otomatik hazirlanmasi icin gelistirilmis Flask tabanli planlama uygulamasi.

Proje; ders, derslik, ogrenci, ogretim uyesi ve ozel durum bilgilerini kullanarak cakismasiz ve kapasiteye uygun sinav programlari uretmeyi amaclar.

## Ozellikler

- Kullanici rolleri: admin, bolum yetkilisi, ogretim uyesi ve ogrenci
- Ders ve derslik yonetimi
- Ozel durum ve uygunluk girisi
- Otomatik sinav programi olusturma
- PDF ve Excel raporlama
- Flask-Login ile kimlik dogrulama

## Teknolojiler

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-WTF
- SQLite
- ReportLab
- OpenPyXL / xlrd

## Kurulum

```bash
git clone https://github.com/Wrindzler/uni_sinav_sistemi.git
cd uni_sinav_sistemi
pip install -r requirements.txt
python app.py
```

Uygulamayi tarayicida acmak icin:

```text
http://localhost:5000
```

## Varsayilan Admin

```text
Kullanici adi: admin
Sifre: admin123
```

> Not: Varsayilan sifre sadece gelistirme ve test ortami icindir.
