# ==========================================
# KUMPULAN IMPORT LIBRARY (VERSI WEB FINAL)
# ==========================================
import streamlit as st          
import plotly.graph_objects as go 
import pandas as pd             
import hashlib                  
import threading                
import time                     
import json                     
import base64                   
from datetime import datetime   

# ==========================================
# CONFIGURASI UI THEME (HIGH CONTRAST WEB HUD)
# ==========================================
st.set_page_config(page_title="Cloud Tuning Garage HUD", page_icon="🏁", layout="wide")

# Perbaikan paksa warna font dan background sidebar agar terlihat sangat jelas di HP/Web
st.markdown("""
    <style>
    /* Background Utama Website */
    .main { 
        background-color: #0c0d10; 
        color: #ffffff; 
    }
    
    /* PAKSA SIDEBAR (BAGIAN KIRI) AGAR SANGAT JELAS & KONTRAS */
    [data-testid="stSidebar"] {
        background-color: #1a1d26 !important; /* Warna abu-abu gelap solid, bukan hitam pekat */
        border-right: 3px solid #ff5722 !important; /* Garis pembatas oranye tegas */
    }
    
    /* Paksa semua teks di dalam sidebar agar berwarna putih terang/oranye */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Warna teks input box di dalam sidebar */
    [data-testid="stSidebar"] input {
        color: #ffffff !important;
        background-color: #10121a !important;
        border: 1px solid #ff5722 !important;
    }
    
    /* Judul Utama */
    h1, h2, h3 { 
        color: #ff5722 !important; 
        font-family: 'Impact', 'Arial Black', sans-serif; 
        letter-spacing: 1px;
    }
    
    /* Kartu List Komponen */
    .rpg-row {
        background-color: #181b24;
        border: 2px solid #282d3d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .part-title {
        font-size: 20px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 5px;
    }
    .category-tag {
        background-color: #ff5722;
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .stat-label {
        color: #a0a5b5;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stat-value {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
    }
    .status-badge-inline {
        padding: 6px 12px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 14px;
        text-align: center;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# MASTER DATA KATEGORI & KOMPONEN
# ==========================================
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

# ==========================================
# WEB CLOUD STORAGE INITIALIZATION
# ==========================================
if "garasi_data" not in st.session_state:
    st.session_state["garasi_data"] = {}

# ==========================================
# SIDEBAR CONTROLLER
# ==========================================
st.sidebar.markdown("# 🏁 CLOUD GARAGE")
st.sidebar.markdown("---")
nama_motor = st.sidebar.text_input("MODEL MOTOR", value="HONDA CBR 250RR")
odo_now = st.sidebar.number_input("ODOMETER SEKARANG (KM)", min_value=0, value=25000)
km_harian = st.sidebar.slider("JARAK TEMPUH HARIAN (KM)", min_value=5, max_value=200, value=40)

hash_garasi = hashlib.sha256(nama_motor.encode()).hexdigest()[:10].upper()
st.sidebar.write(f"🔑 **WEB CHASSIS ID:** WEB-{hash_garasi}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ BACKUP TOOLKIT")

uploaded_file = st.sidebar.file_uploader("Import Data Garasi (.json)", type=["json"])
if uploaded_file is not None:
    try:
        loaded_data = json.load(uploaded_file)
        for k, v in loaded_data.items():
            st.session_state["garasi_data"][k] = v
        st.sidebar.success("✅ Data Berhasil Diimport!")
    except Exception:
        st.sidebar.error("❌ File JSON Tidak Valid.")

if st.sidebar.button("🗑️ RESET ALL DATA WEB"):
    st.session_state["garasi_data"] = {}
    st.rerun()

# ==========================================
# CALCULATION & ENGINE ENGINE CORE
# ==========================================
semua_hasil_part = []
skor_sistem = {kategori: [] for kategori in MASTER_KOMPONEN.keys()}

st.write("### 📝 1. PANEL ESTIMASI PEMASANGAN SPEREPART")
st.info("💡 Data yang Anda isi di bawah ini tersimpan aman di browser selama tab tidak ditutup. Unduh file JSON di bagian bawah untuk menyimpan cadangan permanen.")

with st.expander("⚙️ KLIK UNTUK INPUT DATA KILOMETER & TANGGAL PASANG SPEREPART"):
    for kategori, list_part in MASTER_KOMPONEN.items():
        st.markdown(f"#### 🔹 Kategori: {kategori}")
        for part in list_part:
            
            state_key_odo = f"state_o_{part['id']}"
            state_key_tgl = f"state_t_{part['id']}"
            
            saved_odo = st.session_state["garasi_data"].get(state_key_odo, max(0, odo_now - 2000))
            saved_tgl_str = st.session_state["garasi_data"].get(state_key_tgl, datetime.now().strftime("%Y-%m-%d"))
            saved_tgl = datetime.strptime(saved_tgl_str, "%Y-%m-%d")

            c_name, c_odo, c_tgl = st.columns([2, 2, 2])
            with c_name:
                st.markdown(f"<p style='padding-top:35px; font-weight:bold;'>{part['nama']}</p>", unsafe_allow_html=True)
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
                status, warna, teks_warna = "CRITICAL", "#ff3333", "#ffffff"
            elif persen_sisa <= 25 or sisa_hari_real <= 14:
                status, warna, teks_warna = "WARNING", "#ffcc00", "#121214"
            else:
                status, warna, teks_warna = "GOOD", "#00ffcc", "#121214"

            semua_hasil_part.append({
                "kategori": kategori, "nama": part["nama"], "sisa_km": sisa_km_real,
                "sisa_hari": sisa_hari_real, "persen": persen_sisa, "status": status, 
                "warna": warna, "teks_warna": teks_warna
            })
            skor_sistem[kategori].append(persen_sisa)

# ==========================================
# MAIN GRAPHICS & RADAR DISPLAY
# ==========================================
st.markdown("---")
st.title("🎛️ 2. TELEMETRI DIAGNOSTIK WEB HANGAR")

col_radar, col_stats = st.columns([2, 3])

with col_radar:
    kategori_radar = list(skor_sistem.keys())
    nilai_radar = [round(sum(skor_sistem[kat])/len(skor_sistem[kat])) for kat in kategori_radar]
    kategori_radar.append(kategori_radar[0])
    nilai_radar.append(nilai_radar[0])

    fig = go.Figure(data=go.Scatterpolar(r=nilai_radar, theta=kategori_radar, fill='toself', fillcolor='rgba(255, 87, 34, 0.2)', line=dict(color='#ff5722', width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#333"), angularaxis=dict(gridcolor="#333")), showlegend=False, height=300, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart
