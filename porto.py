import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from fpdf import FPDF
import streamlit as st
import io
import re
import os

# Data Alometrik untuk Jenis Pohon
persamaan_alometrik = {
    "Akasia (Acacia spp.)": {"a": 0.072 , "b": 2.54},
    "Beringin (Ficus benghalensis)": {"a": 0.123 , "b": 2.35},
    "Jati (Tectona grandis)": {"a": 0.055, "b": 2.579},
    "Mahoni (Swietenia mahagoni)": {"a": 0.048, "b": 2.68},
    "Pinus (Pinus spp.)": {"a": 0.052, "b": 2.64},
    "Sengon (Falcataria moluccana)": {"a": 0.148, "b": 2.299},
    "Trembesi (Albizia saman)": {"a": 0.167, "b": 2.371}
}

jenis_pohon_list = list(persamaan_alometrik.keys())
bulan_list = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# Inisialisasi data dummy hanya jika belum ada atau jumlah data kurang dari 60
if "data_dummy" not in st.session_state:
    np.random.seed(42) # agar hasil random data dummy tetap sama

    #inisiasi DBH awal setiap pohon
    dbh_awal = {jenis: np.random.uniform(10, 26, size=3) for jenis in jenis_pohon_list}  # 3 pohon per jenis
    data_dummy = pd.DataFrame(columns=["Bulan", "Jenis Pohon", "DBH", "Biomassa", "Karbon", "Serapan CO2"])
    
    for bulan in bulan_list:
        for jenis_pohon in jenis_pohon_list:
            for i in range(3):  # 5 pohon per bulan
                pertumbuhan = np.random.uniform(0,1)
                dbh_awal[jenis_pohon][i] += pertumbuhan 
                dbh = dbh_awal[jenis_pohon][i]
                a, b = persamaan_alometrik[jenis_pohon]["a"], persamaan_alometrik[jenis_pohon]["b"]
            
                biomassa = a * (dbh ** b)
                karbon = biomassa * 0.48
                co2t = karbon * 3.67
            
                new_data = pd.DataFrame([[bulan, jenis_pohon, dbh, biomassa, karbon, co2t]], 
                                    columns=["Bulan", "Jenis Pohon", "DBH", "Biomassa", "Karbon", "Serapan CO2"])
                data_dummy = pd.concat([data_dummy, new_data], ignore_index=True)
    
    st.session_state.data_dummy = data_dummy

# Fungsi untuk menyimpan data ke file CSV
def simpan_data_ke_csv():
    st.session_state.data_dummy.to_csv("data_karbon.csv", index=False)

# Fungsi untuk memuat data dari file CSV
def muat_data_dari_csv():
    if os.path.exists("data_karbon.csv"):
        return pd.read_csv("data_karbon.csv")
    else:
        return pd.DataFrame(columns=["Bulan", "Jenis Pohon", "DBH", "Biomassa", "Karbon", "Serapan CO2"])

# Inisialisasi data dummy dari file CSV (jika ada)
if "data_dummy" not in st.session_state:
    st.session_state.data_dummy = muat_data_dari_csv()

def validasi_nama_pohon(nama):
    """
    Validasi nama pohon:
    - Tidak boleh kosong.
    - Hanya boleh mengandung huruf dan spasi.
    """
    if not nama.strip():  # Cek apakah input kosong atau hanya spasi
        return False
    # Cek apakah input hanya mengandung huruf dan spasi
    if not re.match(r"^[A-Za-z\s]+$", nama):
        return False
    return True


# streamlite interface
st.title("🌳 Kalkulator Serapan Karbon")

# menu utama streamlit
menu = st.selectbox("Pilih Menu", ["Hitung Serapan Karbon", 
                                   "Tren Perbandingan Karbon dalam Satu Tahun",
                                   "Tampilkan Data yang Tersimpan",
                                   "Simpan Hasil Perhitungan ke CSV", 
                                   "Generate Dashboard Data Karbon PDF"])

# Fungsi menghitung biomassa, karbon, dan CO2
if menu == "Hitung Serapan Karbon":
    jenis_pohon = st.selectbox("Pilih Jenis Pohon", jenis_pohon_list + ["Pohon Bercabang Lainnya"])
    
    if jenis_pohon == "Pohon Bercabang Lainnya":
        nama_pohon = st.text_input("Masukkan Nama Pohon").strip()
        if nama_pohon:
            if not validasi_nama_pohon(nama_pohon):
                st.error("❌ Nama pohon tidak valid. Hanya boleh mengandung huruf dan spasi.")
            else:
                jenis_pohon = nama_pohon.title()
        else:
            st.error("❌ Nama pohon tidak boleh kosong.")

    dbh = st.number_input("Masukkan DBH (cm)", min_value=1.0)

    # Input bulan dari pengguna
    bulan_sekarang = st.selectbox("Pilih Bulan", bulan_list)  # Pengguna memilih bulan
    
    biomassa = karbon = co2t = None  # Inisiasi variabel perhitungan sebelum tombol "hitung karbon" ditekan

    if st.button("Hitung Karbon"):
        if jenis_pohon in persamaan_alometrik:
            a = persamaan_alometrik[jenis_pohon]["a"]
            b = persamaan_alometrik[jenis_pohon]["b"]
        else: 
            a = 0.11
            b = 2.62
                    
        biomassa = a * (dbh ** b)
        karbon = biomassa * 0.48  # Asumsi %C = 48%
        co2t = karbon * 3.67

        st.write(f"Bulan: {bulan_sekarang}")
        st.write(f"Jenis Pohon: {jenis_pohon}")
        st.write(f"DBH: {dbh} cm")

        st.write(f"Total Biomassa: {biomassa:.2f} kg")
        st.write(f"Total Serapan Karbon: {karbon:.2f} kg")
        st.write(f"Serapan CO2: {co2t:.2f} kg")

        # Tanya pengguna apakah ingin menyimpan data menggunakan checkbox
        st.session_state.temp_data = {
            "Bulan": bulan_sekarang,
            "Jenis Pohon": jenis_pohon,
            "DBH": dbh,
            "Biomassa": biomassa,
            "Karbon": karbon,
            "Serapan CO2": co2t
        }

    # Tampilkan opsi untuk menyimpan data
    if "temp_data" in st.session_state:
        save_data = st.selectbox("Apakah Anda ingin menyimpan data ini?", ["Ya", "Tidak"])

        if save_data == "Ya":
            # Append data sementara ke dataframe
            new_data = pd.DataFrame([st.session_state.temp_data])
            st.session_state.data_dummy = pd.concat([st.session_state.data_dummy, new_data], ignore_index=True)
            st.success("✅ Data berhasil ditambahkan!")
            del st.session_state.temp_data  # Hapus data sementara setelah disimpan
            simpan_data_ke_csv()
        elif save_data == "Tidak":
            st.info("ℹ️ Data tidak disimpan dan akan hilang saat halaman dimuat ulang (refresh).")
            del st.session_state.temp_data  # Hapus data sementara jika tidak disimpan

# Fungsi untuk menampilkan data karbon dummy
elif menu == "Tampilkan Data yang Tersimpan":
    st.write("📊 Data Perhitungan Karbon yang Tersimpan")
    st.write(st.session_state.data_dummy)  # Menampilkan tabel tanpa indeks

    # fitur filter berdasarkan jenis pohon
    jenis_pohon_filter = st.selectbox("Filter Berdasarkan Jenis Pohon", ["Semua"] + jenis_pohon_list + ["Pohon Bercabang Lainnya"])
    
    if jenis_pohon_filter == "Semua":
        st.write(st.session_state.data_dummy)  # Tampilkan semua data
    elif jenis_pohon_filter == "Pohon Bercabang Lainnya":
        # Tampilkan data dengan jenis pohon yang tidak ada di jenis_pohon_list
        filtered_data = st.session_state.data_dummy[~st.session_state.data_dummy["Jenis Pohon"].isin(jenis_pohon_list)]
        st.write(filtered_data)
    else:
        filtered_data = st.session_state.data_dummy[st.session_state.data_dummy["Jenis Pohon"] == jenis_pohon_filter]
        st.write(filtered_data)

# Fungsi untuk menampilkan tren karbon dalam satu tahun
elif menu == "Tren Perbandingan Karbon dalam Satu Tahun":
    if "data_dummy" in st.session_state and not st.session_state.data_dummy.empty:
        karbon_tahunan = st.session_state.data_dummy.groupby("Bulan")["Karbon"].mean().reset_index()
    else:
        st.error("⚠️ Data belum tersedia! Pastikan data telah dibuat sebelum melihat tren karbon.")
        st.stop()
        
    # mapping bulan ke angka agar urutannya sesuai
    bulan_mapping = {bulan: i+1 for i, bulan in enumerate(bulan_list)}

    # Tambahkan kolom numerik untuk urutan bulan
    karbon_tahunan["Bulan_Numerik"] = karbon_tahunan["Bulan"].map(bulan_mapping)
    karbon_tahunan = karbon_tahunan.sort_values("Bulan_Numerik")

    # hapus kolom tabel numerik sebelum tabel ditampilkan
    karbon_tahunan_tampil = karbon_tahunan.drop(columns=["Bulan_Numerik"])

    #reset index dan menghapus kolom index lama
    karbon_tahunan_tampil = karbon_tahunan_tampil.reset_index(drop=True)

    # clear figure sebelum membuat plot baru
    plt.clf()

    # Menampilkan grafik tren karbon
    plt.figure(figsize=(10, 5))
    plt.plot(karbon_tahunan["Bulan"], karbon_tahunan["Karbon"], marker="o", linestyle="-", color="green", label="Karbon (kg)")
    plt.xlabel("Bulan")
    plt.ylabel("Rerata Karbon (kg)")
    plt.title("Tren Karbon dalam 1 Tahun")
    plt.legend()
    plt.grid(True)

    # Simpan grafik sebagai gambar
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format="png", bbox_inches="tight", dpi=300)
    plt.close()

    # Kembalikan pointer ke awal
    img_bytes.seek(0)
    
    # Simpan BytesIO ke session state untuk digunakan di menu lain
    st.session_state.tren_karbon_img = img_bytes.getvalue()

    # Menampilkan grafik di Streamlit
    st.image(img_bytes)

    # Analisis otomatis tren karbon
    karbon_awal = karbon_tahunan.iloc[0]["Karbon"]  # Nilai karbon di bulan pertama
    karbon_akhir = karbon_tahunan.iloc[-1]["Karbon"]  # Nilai karbon di bulan terakhir
    rata_rata_karbon = karbon_tahunan["Karbon"].mean()

    # Menampilkan hasil rerata dalam tabel
    if len(karbon_tahunan_tampil.columns) == 2:
        karbon_tahunan_tampil.columns = ["Bulan", "Rata-rata Karbon (kg)"]
    st.write("📊 **Rata-rata Karbon per Bulan:**")
    st.write(karbon_tahunan_tampil)

    st.write(f"🔍 Rata-rata karbon dalam setahun: {rata_rata_karbon:.2f} kg")


    # 1. Perbandingan Bulan Awal & Akhir
    if karbon_akhir > karbon_awal:
        st.success("✅ Tren karbon meningkat sepanjang tahun.")
    elif karbon_akhir < karbon_awal:
        st.warning("🔻 Tren karbon menurun dibandingkan awal tahun.")
    else:
        st.info("➖ Tren karbon stabil sepanjang tahun.")

    # 2. Pola Kenaikan & Penurunan
    perubahan = np.diff(karbon_tahunan["Karbon"])  # Selisih antar bulan
    jumlah_naik = np.sum(perubahan > 0)  # Berapa kali karbon naik?
    jumlah_turun = np.sum(perubahan < 0)  # Berapa kali karbon turun?

    if jumlah_naik > jumlah_turun:
        st.success("📈 Karbon lebih sering mengalami kenaikan dibanding penurunan.")
    elif jumlah_naik < jumlah_turun:
        st.warning("📉 Karbon lebih sering mengalami penurunan dibanding kenaikan.")
    else:
        st.info("⚖️ Karbon mengalami fluktuasi yang seimbang sepanjang tahun.")

    # 3. Kesimpulan Akhir
    if karbon_akhir > karbon_awal and jumlah_naik > jumlah_turun:
        st.success("🔥 Kesimpulan: Karbon mengalami tren meningkat dengan kenaikan signifikan sepanjang tahun.")
    elif karbon_akhir < karbon_awal and jumlah_turun > jumlah_naik:
        st.warning("🌱 Kesimpulan: Karbon mengalami tren menurun, kemungkinan karena faktor ekologi atau penebangan.")
    else:
        st.info("🔄 Kesimpulan: Karbon mengalami fluktuasi dengan perubahan yang tidak terlalu signifikan.")


# Fungsi untuk menyimpan hasil ke CSV
elif menu == "Simpan Hasil Perhitungan ke CSV":
    st.session_state.data_dummy.to_csv("data_karbon.csv", index=False)
    st.success("✅ Data berhasil disimpan ke data_karbon.csv!")
    with open("hasil_karbon.csv", "rb") as file:
        st.download_button("Unduh CSV", file, file_name="data_karbon.csv", mime="text/csv")


elif menu == "Generate Dashboard Data Karbon PDF":
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Laporan Perhitungan Karbon", ln=True, align="C")

        # Ringkasan Data
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Total Data Pohon: {len(st.session_state.data_dummy)}", ln=True)
        pdf.cell(0, 10, f"Rata-rata Karbon (kg): {st.session_state.data_dummy['Karbon'].mean():.2f}", ln=True)
        pdf.cell(0, 10, f"Total Karbon yang Diserap (kg): {st.session_state.data_dummy['Karbon'].sum():.2f}", ln=True)

        # Menambahkan Rata-rata Karbon per Jenis Pohon
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Rata-rata Karbon per Jenis Pohon:", ln=True)

        rata_rata_karbon_per_pohon = st.session_state.data_dummy.groupby("Jenis Pohon")["Karbon"].mean()

        pdf.set_font("Arial", "", 12)
        for jenis, rata2 in rata_rata_karbon_per_pohon.items():
            pdf.cell(0, 10, f"- {jenis}: {rata2:.2f} kg", ln=True)

        # Tambahkan Grafik Tren Karbon
        if "tren_karbon_img" in st.session_state:
            with open("tren_karbon.png", "wb") as f:
                f.write(st.session_state.tren_karbon_img)
            
            # sisipkan grafik ke PDF
            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Grafik Tren Karbon dalam 1 Tahun:", ln=True)
            pdf.image("tren_karbon.png", x=10, y=None, w=190)  # Sisipkan grafik
        
        else:
            st.error("❌ Grafik tren karbon tidak ditemukan. Kunjungi menu tren karbon terlebih dahulu untuk generate karbon")

        # Tambahkan Header Tabel
        pdf.ln(10)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(30, 10, "Bulan", border=1)
        pdf.cell(40, 10, "Jenis Pohon", border=1)
        pdf.cell(30, 10, "DBH (cm)", border=1)
        pdf.cell(30, 10, "Karbon (kg)", border=1)
        pdf.cell(40, 10, "Serapan CO2 (kg)", border=1)
        pdf.ln()

        # Tambahkan Data ke Tabel
        pdf.set_font("Arial", "", 10)
        for i in range(len(st.session_state.data_dummy)):
            pdf.cell(20, 10, str(st.session_state.data_dummy.iloc[i]["Bulan"]), border=1)
            pdf.cell(60, 10, str(st.session_state.data_dummy.iloc[i]["Jenis Pohon"]), border=1)
            pdf.cell(20, 10, f"{st.session_state.data_dummy.iloc[i]['DBH']:.2f}", border=1)
            pdf.cell(30, 10, f"{st.session_state.data_dummy.iloc[i]['Biomassa']:.2f}", border=1)
            pdf.cell(30, 10, f"{st.session_state.data_dummy.iloc[i]['Karbon']:.2f}", border=1)
            pdf.cell(30, 10, f"{st.session_state.data_dummy.iloc[i]['Serapan CO2']:.2f}", border=1)
            pdf.ln()

        # Simpan sebagai PDF
        pdf.output("Laporan_Karbon.pdf")
        st.success("✅ Laporan berhasil dibuat! Lihat file 'Laporan_Karbon.pdf'.")

        with open("Laporan_Karbon.pdf", "rb") as pdf_file:
            st.download_button("Unduh Laporan PDF", pdf_file, file_name="Laporan_Karbon.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {e}")
