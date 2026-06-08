import streamlit as st          
import plotly.graph_objects as go 
import pandas as pd             
import hashlib                  
import json                     
from datetime import datetime   

# Konfigurasi halaman dasar
st.set_page_config(page_title="Garage HUD Cloud", page_icon="🏁", layout="wide")

# Master data komponen
MASTER_KOMPONEN = {
    "Mesin Utama": [
        {"id": "eng_oli", "nama": "Oli Mesin", "limit_km": 3000, "limit_bulan": 2},
        {"id": "eng_filter_oli", "nama": "Filter Oli", "limit_km": 10000, "limit_bulan": None},
        {"id": "eng_keteng", "nama": "Rantai Keteng", "limit_km": 40000, "limit_bulan": None}
    ],
    "Transmisi / CVT": [
        {"id": "drv_vbelt", "nama": "V-Belt Penggerak", "limit_km": 24000, "limit_bulan": 24},
        {"id": "drv_roller", "nama": "Roller CVT", "limit_km": 12000, "limit_bulan": None},
        {"id": "drv_oli_gardan", "nama": "Oli Gardan", "limit_km": 8000, "limit_bulan": 6}
    ],
    "Bahan Bakar": [
        {"id": "fl_busi", "nama": "Busi Motor", "limit_km": 10000, "limit_bulan": 12},
        {"id": "fl_filter_udara", "nama": "Filter Udara", "limit_km": 12000, "limit_bulan": 12}
    ],
    "Pengereman": [
        {"id": "brk_kampas_depan", "nama": "Kampas Rem Depan", "limit_km": 12000, "limit_bulan": None},
        {"id": "brk_minyak_rem", "nama": "Minyak Rem Hidrolik", "limit_km": 20000, "limit_bulan": 24}
    ],
    "Sistem Pendingin": [
        {"id": "cl_coolant", "nama": "Air Radiator (Coolant)", "limit_km": 12000, "limit_bulan": 12}
    ],
    "Kelistrikan ⚡": [
        {"id": "el_aki", "nama": "Aki Motor Utama", "limit_km": None, "limit_bulan": 24}
    ],
    "Sasis & Roda 🏍️": [
        {"id": "ch_ban_depan", "nama": "Ban Luar Depan", "limit_km": 30000, "limit_bulan": 36},
        {"id": "ch_ban_belakang", "nama": "Ban Luar Belakang", "limit_km": 30000, "limit_bulan": 36}
    ]
}

if "garasi_data" not in st.session_state:
    st.session_state["garasi_data"] = {}

# Sidebar Kiri
st.sidebar.title("🏁 CLOUD GARAGE")
st.sidebar.write("---")
nama_motor = st.sidebar.text_input("MODEL MOTOR", value="HONDA CBR 250RR")
odo_now = st.sidebar.number_input("ODOMETER SEKARANG (KM)", min_value=0, value=25000)
km_harian = st.sidebar.slider("JARAK TEMPUH HARIAN (KM)", min_value=5, max_value=200, value=40)

hash_garasi = hashlib.sha256(nama_motor.encode()).hexdigest()[:10].upper()
st.sidebar.write(f"🔑 **CHASSIS ID:** WEB-{hash_garasi}")

st.sidebar.write("---")
st.sidebar.subheader("🛠️ BACKUP TOOLKIT")
uploaded_file = st.sidebar.file_uploader("Import Data Garasi (.json)", type=["json"])
if uploaded_file is not None:
    try:
        st.session_state["garasi_data"] = json.load(uploaded_file)
        st.sidebar.success("✅ Data Berhasil Diimport!")
    except:
        st.sidebar.error("❌ File tidak valid.")

if st.sidebar.button("🗑️ RESET ALL DATA"):
    st.session_state["garasi_data"] = {}
    st.rerun()

# Pemrosesan Data
semua_hasil_part = []
skor_sistem = {kategori: [] for kategori in MASTER_KOMPONEN.keys()}

st.subheader("📝 1. PANEL INPUT DATA SPAREPART")
with st.expander("⚙️ KLIK DI SINI UNTUK MENGISI ODO / TANGGAL PASANG KOMPONEN", expanded=False):
    for kategori, list_part in MASTER_KOMPONEN.items():
        st.markdown(f"**🔹 Kategori: {kategori}**")
        for part in list_part:
            state_key_odo = f"state_o_{part['id']}"
            state_key_tgl = f"state_t_{part['id']}"
            
            saved_odo = st.session_state["garasi_data"].get(state_key_odo, max(0, odo_now - 2000))
            saved_tgl_str = st.session_state["garasi_data"].get(state_key_tgl, datetime.now().strftime("%Y-%m-%d"))
            saved_tgl = datetime.strptime(saved_tgl_str, "%Y-%m-%d")

            c_name, c_odo, c_tgl = st.columns([2, 2, 2])
            with c_name:
                st.write(f"**{part['nama']}**")
            with c_odo:
                o_pasang = st.number_input(f"Odo Pasang (Km)", min_value=0, max_value=odo_now, value=int(saved_odo), key=f"o_{part['id']}")
            with c_tgl:
                t_pasang = st.date_input(f"Tanggal Pasang", value=saved_tgl, key=f"t_{part['id']}")
            
            st.session_state["garasi_data"][state_key_odo] = o_pasang
            st.session_state["garasi_data"][state_key_tgl] = t_pasang.strftime("%Y-%m-%d")

            km_jalan = odo_now - o_pasang
            persen_km = ((part["limit_km"] - km_jalan) / part["limit_km"]) * 100 if part["limit_km"] else 100
            
            bln_jalan = (datetime.now().year - t_pasang.year) * 12 + (datetime.now().month - t_pasang.month)
            persen_bln = ((part["limit_bulan"] - bln_jalan) / part["limit_bulan"]) * 100 if part["limit_bulan"] else 100
            
            persen_sisa = max(0, min(100, round(min(persen_km, persen_bln))))
            sisa_km_real = (part["limit_km"] - km_jalan) if part["limit_km"] else "PERMANEN"
            
            sisa_hari_real = round(sisa_km_real / km_harian) if isinstance(sisa_km_real, int) else 9999
            if part["limit_bulan"]:
                sisa_hari_bln = (part["limit_bulan"] - bln_jalan) * 30
                sisa_hari_real = min(sisa_hari_real, sisa_hari_bln)

            if (isinstance(sisa_km_real, int) and sisa_km_real <= 0) or persen_sisa <= 0:
                status = "CRITICAL"
            elif persen_sisa <= 25 or sisa_hari_real <= 14:
                status = "WARNING"
            else:
                status = "GOOD"

            semua_hasil_part.append({
                "kategori": kategori, "nama": part["nama"], "sisa_km": sisa_km_real,
                "sisa_hari": sisa_hari_real, "persen": persen_sisa, "status": status
            })
            skor_sistem[kategori].append(persen_sisa)

# Tampilan Utama Telemetri
st.write("---")
st.header("🎛️ 2. TELEMETRI DIAGNOSTIK KENDARAAN")

col_radar, col_stats = st.columns([1, 1])

with col_radar:
    kategori_radar = list(skor_sistem.keys())
    nilai_radar = [round(sum(skor_sistem[kat])/len(skor_sistem[kat])) for kat in kategori_radar]
    kategori_radar.append(kategori_radar[0])
    nilai_radar.append(nilai_radar[0])

    fig = go.Figure(data=go.Scatterpolar(r=nilai_radar, theta=kategori_radar, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=280)
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    total_health = round(sum([p["persen"] for p in semua_hasil_part]) / len(semua_hasil_part))
    st.metric(label="KESEHATAN TOTAL MOTOR", value=f"{total_health}%")
    if total_health >= 80:
        st.success("🔥 KONDISI MOTOR SANGAT PRIMA")
    elif total_health >= 50:
        st.warning("🔧 MOTOR BUTUH SERVIS / MAINTENANCE")
    else:
        st.error("🚨 BAHAYA! KONDISI MOTOR KRITIS")

# Tabel Status Live
st.write("---
