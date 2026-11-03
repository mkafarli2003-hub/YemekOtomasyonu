import sqlite3
from tkinter import *
from tkinter import messagebox

# Katılım Ekranı Penceresi
pencere = Tk()
pencere.title("Yemek Gecesi - Katılım ve Refakatçi Bildirim Formu")
pencere.geometry("450x500")


def katilimi_kaydet():
  email = email_giris.get()
  durum = katilim_durumu.get()  # 'Katılacak' veya 'Katılmayacak'
  refakatci_var_mi = ref_durumu.get()  # 'Evet' veya 'Hayır'
  ref_ad_val = ref_ad_giris.get()

  if not email:
    messagebox.showerror("Hata", "Lütfen e-posta adresinizi girin!")
    return

  conn = sqlite3.connect("yemek_otomasyonu.db")
  cursor = conn.cursor()

  # 1. Önce bu e-posta ile kayıtlı çalışan var mı kontrol et
  cursor.execute(
      "SELECT calisan_id, ad, soyad FROM Calisan WHERE email = ?", (email,)
  )
  calisan = cursor.fetchone()

  if not calisan:
    messagebox.showerror(
        "Hata",
        "Bu e-posta ile kayıtlı çalışan bulunamadı! Önce kayıt olmalısınız.",
    )
    conn.close()
    return

  calisan_id = calisan[0]
  calisan_ad_soyad = f"{calisan[1]} {calisan[2]}"

  try:
    # 2. Etkinlik tablosundan aktif etkinliği al (İlk etkinliği seçiyoruz)
    cursor.execute("SELECT etkinlik_id, kisi_basi_ucret FROM Etkinlik LIMIT 1")
    etkinlik = cursor.fetchone()

    if not etkinlik:
      messagebox.showerror(
          "Hata", "Sistemde kayıtlı aktif etkinlik bulunamadı!"
      )
      conn.close()
      return

    etkinlik_id = etkinlik[0]
    ucret = etkinlik[1]

    # Toplam kişi ve tutar hesaplama
    toplam_kisi = 1
    if refakatci_var_mi == "Evet":
      toplam_kisi = 2
      toplam_tutar = ucret * 2
    else:
      toplam_tutar = ucret

    # 3. Katilim tablosuna kaydet (Varsa güncelle)
    cursor.execute(
        """
            INSERT INTO Katilim (calisan_id, etkinlik_id, katilim_durumu, toplam_kisi_sayisi, odeme_durumu)
            VALUES (?, ?, ?, ?, 'Beklemede')
            ON CONFLICT(calisan_id, etkinlik_id) 
            DO UPDATE SET katilim_durumu=excluded.katilim_durumu, toplam_kisi_sayisi=excluded.toplam_kisi_sayisi
        """,
        (calisan_id, etkinlik_id, durum, toplam_kisi),
    )

    # Katılım ID'yi al
    cursor.execute(
        "SELECT katilim_id FROM Katilim WHERE calisan_id = ? AND etkinlik_id = ?",
        (calisan_id, etkinlik_id),
    )
    katilim_id_val = cursor.fetchone()[0]

    # 4. Eğer refakatçi varsa Refakatci tablosuna ekle
    if refakatci_var_mi == "Evet" and ref_ad_val:
      cursor.execute(
          """
                INSERT INTO Refakatci (katilim_id, ad, tur, yas)
                VALUES (?, ?, 'Misafir', 25)
            """,
          (katilim_id_val, ref_ad_val),
      )

    # 5. Ödeme tablosuna borç olarak yansıt
    cursor.execute(
        """
            INSERT INTO Odeme (katilim_id, tutar, yontem, durum)
            VALUES (?, ?, 'Nakit/Elden', 'Beklemede')
            ON CONFLICT(katilim_id) DO UPDATE SET tutar=excluded.tutar
        """,
        (katilim_id_val, toplam_tutar),
    )

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Başarılı",
        f"Sayın {calisan_ad_soyad},\nKatılım durumunuz kaydedildi!\nToplam"
        f" Tutar: {toplam_tutar} TL",
    )

  except Exception as e:
    messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


# --- ARAYÜZ TASARIMI ---
Label(
    pencere, text="Yemek Gecesi Katılım Formu", font=("Arial", 14, "bold")
).pack(pady=10)

Label(pencere, text="Sisteme Kayıtlı E-posta Adresiniz:").pack()
email_giris = Entry(pencere, width=30)
email_giris.pack(pady=5)

Label(pencere, text="Yemek Gecesine Katılacak mısınız?").pack(pady=5)
katilim_durumu = StringVar(value="Katılacak")
Radiobutton(
    pencere, text="Evet, Katılacağım", variable=katilim_durumu, value="Katılacak"
).pack()
Radiobutton(
    pencere,
    text="Hayır, Katılamayacağım",
    variable=katilim_durumu,
    value="Katılmayacak",
).pack()

Label(pencere, text="Yanınızda Refakatçi Getirecek misiniz?").pack(pady=5)
ref_durumu = StringVar(value="Hayır")
Radiobutton(
    pencere, text="Evet (1 Kişi)", variable=ref_durumu, value="Evet"
).pack()
Radiobutton(pencere, text="Hayır", variable=ref_durumu, value="Hayır").pack()

Label(pencere, text="Refakatçi Adı Soyadı (Varsa):").pack()
ref_ad_giris = Entry(pencere, width=30)
ref_ad_giris.pack(pady=5)

# Kaydet Butonu
btn_katilim = Button(
    pencere,
    text="Katılımı Onayla ve Hesapla",
    command=katilimi_kaydet,
    bg="blue",
    fg="white",
    font=("Arial", 10, "bold"),
)
btn_katilim.pack(pady=20)

pencere.mainloop()