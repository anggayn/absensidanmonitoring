from flask import Flask, render_template, request, redirect, url_for, session, make_response,flash, jsonify, Response, current_app
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy import or_
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from datetime import datetime, date, time  
from sqlalchemy import func
import pandas as pd
from werkzeug.utils import secure_filename
from flask import send_file
import zipfile
import io
import shutil

# import Secure File
from werkzeug.utils import secure_filename

# Import Sound
import threading
import pygame

# Import Library untuk Operasi Sistem dan Manipulasi String
import os
import re

# Import Library untuk Operasi Keamanan
import random
import string
from werkzeug.security import generate_password_hash
import uuid

# Import Library untuk Threading dan Operasi Waktu
import threading
from datetime import datetime, date, time as dt_time, timedelta
import time

# Import Library Utama
import argparse
import cv2  # type: ignore
import numpy as np  # type: ignore

# Import Library untuk Model YOLO
from ultralytics import YOLO  # type: ignore

# import Library wa
import requests
import base64

# import pdf
from flask import send_file
from fpdf import FPDF

# import Library wa
import base64
from sqlalchemy import or_, String

app = Flask(__name__, template_folder='pages')

app.secret_key = 'your_secret_key'

# Konfigurasi koneksi database (ubah sesuai kebutuhan)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/absensidanmonitoring'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi database
db = SQLAlchemy(app)
models_by_admin = {}  
class_names_by_admin = {}
model_pelanggaran_by_admin = {} 
migrate = Migrate(app, db) 


# whatshapp

ULTRAMSG_INSTANCE_ID = 'instance109410'
ULTRAMSG_API_TOKEN = 'fe469dynm6jlqgaj'

def encode_image_to_base64(image_path):
    """Mengubah gambar menjadi base64 untuk dikirim melalui WhatsApp."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def send_whatsapp_message(person_name, category, timestamp, role_kamera, image_path):
    """Mengirim pesan WhatsApp beserta bukti foto berdasarkan data absensi."""
    with app.app_context():
        pegawai = Pegawai.query.filter_by(nama_pegawai=person_name).first()
        if not pegawai or not pegawai.nomor_pegawai:
            print(f"⚠️ Nomor WhatsApp untuk {person_name} tidak ditemukan.")
            return
        
        recipient_number = pegawai.nomor_pegawai

        # Ambil data absensi terbaru
        latest_absensi = AbsensiPegawai.query.filter_by(pegawai_id=pegawai.id).order_by(AbsensiPegawai.tanggal.desc()).first()
        
        if not latest_absensi:
            print(f"⚠️ Data absensi tidak ditemukan untuk {person_name}.")
            return
        
        # Tentukan jenis absensi berdasarkan role kamera
        if role_kamera == "in":
            waktu_presensi = latest_absensi.presensi_datang.strftime("%H:%M:%S") if latest_absensi.presensi_datang else "Tidak Tersedia"
            foto_path = latest_absensi.foto_datang
        elif role_kamera == "out":
            waktu_presensi = latest_absensi.presensi_pulang.strftime("%H:%M:%S") if latest_absensi.presensi_pulang else "Tidak Tersedia"
            foto_path = latest_absensi.foto_pulang
        else:
            print(f"⚠️ Role kamera tidak valid: {role_kamera}")
            return

        # Pesan teks
        message_body = (
            f"📢 *Notifikasi Absensi Pegawai*\n\n"
            f"📌 *Nama:* {person_name}\n"
            f"📌 *Divisi:* {pegawai.divisi}\n"
            f"📌 *Kategori:* {category}\n"
            f"📌 *Tanggal:* {latest_absensi.tanggal.strftime('%d-%m-%Y')}\n"
            f"📌 *Waktu Presensi:* {waktu_presensi}\n"
            f"📌 *Role Kamera:* {role_kamera.upper()}\n\n"
            f"Terima kasih telah melakukan absensi."
        )

        # Kirim pesan teks ke WhatsApp
        text_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
        text_payload = {'token': ULTRAMSG_API_TOKEN, 'to': recipient_number, 'body': message_body}
        requests.post(text_url, data=text_payload)

        # Kirim foto absensi jika tersedia
        if foto_path:
            full_image_path = os.path.join('static', foto_path)
            if os.path.exists(full_image_path):
                encoded_image = encode_image_to_base64(full_image_path)
                image_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/image"
                image_payload = {
                    'token': ULTRAMSG_API_TOKEN,
                    'to': recipient_number,
                    'image': encoded_image,
                    'caption': f"Bukti Absensi {person_name} ({role_kamera.upper()})"
                }
                requests.post(image_url, data=image_payload)
            else:
                print(f"⚠️ File foto tidak ditemukan: {full_image_path}")

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# definisi tabel Pegawai 
class Pegawai(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    nama_pegawai = db.Column(db.String(100), nullable=False)
    nomor_pegawai = db.Column(db.String(50), nullable=False)
    divisi_id = db.Column(db.Integer, db.ForeignKey('divisi.id'), nullable=True)  
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='pegawai')
    folder_path = db.Column(db.String(255), nullable=True)
    photo = db.Column(db.String(255), nullable=True)

    divisi = relationship("Divisi", back_populates="pegawai")
    admin = relationship("Admin", back_populates="pegawai")

    def __repr__(self):
        return f"<Pegawai {self.nama_pegawai} ({self.username})>"

    
# tabel divisi untuk pegawai
class Divisi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_divisi = db.Column(db.String(50), nullable=False, unique=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)  

    admin = relationship("Admin", back_populates="divisi")

    pegawai = relationship("Pegawai", back_populates="divisi", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Divisi {self.nama_divisi}>"

# definisi tabel konfigurasi kamera presensi
class RoleKamera(Enum):
    IN = "in"
    OUT = "out"

class KonfigurasiKamerapresensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    nama_kamera = db.Column(db.String(100), nullable=False, unique=True)
    role_kamera = db.Column(SQLEnum(RoleKamera), nullable=False)  # Hanya bisa "in" atau "out"
    ip_rtsp = db.Column(db.String(255), nullable=False, unique=True)
    jam_mulai_kedatangan = db.Column(db.Time, nullable=False)
    jam_berakhir_kedatangan = db.Column(db.Time, nullable=False)
    jam_mulai_pulang = db.Column(db.Time, nullable=False)
    jam_berakhir_pulang = db.Column(db.Time, nullable=False)

    admin = relationship("Admin", back_populates="konfigurasi_kamera")

    def __repr__(self):
        return f"<KonfigurasiKamerapresensi {self.nama_kamera} ({self.role_kamera.value})>"
    
# definisi tabel absensi kehadiran pegawai
class AbsensiPegawai(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)  
    pegawai_id = db.Column(db.Integer, db.ForeignKey('pegawai.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    presensi_datang = db.Column(db.Time, nullable=False)
    presensi_pulang = db.Column(db.Time)
    status = db.Column(db.String(50))
    jam_kerja = db.Column(db.Time, nullable=False)
    jam_selesai_kerja = db.Column(db.Time, nullable=False)
    jam_lembur = db.Column(db.Time)
    foto_datang = db.Column(db.String(255))
    foto_pulang = db.Column(db.String(255))
    admin = db.relationship('Admin', back_populates='absensi')
    pegawai = db.relationship('Pegawai', backref=db.backref('absensi', lazy=True))
    def __repr__(self):
        return f"<Absensi Pegawai ID {self.pegawai_id} pada {self.tanggal}>"

# definisi tabel lama kerja
class LamaKerja(db.Model):
    __tablename__ = 'lama_kerja'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    pegawai_id = db.Column(db.Integer, db.ForeignKey('pegawai.id'))
    tanggal = db.Column(db.Date)
    nama_pegawai = db.Column(db.String(100))
    divisi = db.Column(db.String(100))
    lama_terdeteksi = db.Column(db.Integer)
    area_cctv = db.Column(db.String(100))
    foto_bukti = db.Column(db.String(255))  # GANTI DARI LargeBinary
    pelanggaran = db.Column(db.String(100))
    foto_pelanggaran = db.Column(db.String(255))  # GANTI DARI LargeBinary

    def __init__(self, admin_id, pegawai_id, tanggal, nama_pegawai, divisi, lama_terdeteksi, area_cctv, foto_bukti=None, pelanggaran=None, foto_pelanggaran=None):
        self.admin_id = admin_id
        self.pegawai_id = pegawai_id
        self.tanggal = tanggal
        self.nama_pegawai = nama_pegawai
        self.divisi = divisi
        self.lama_terdeteksi = lama_terdeteksi
        self.area_cctv = area_cctv
        self.foto_bukti = foto_bukti
        self.pelanggaran = pelanggaran
        self.foto_pelanggaran = foto_pelanggaran

# definisi tabel konfigurasi kamera pelacakan kerja
class KonfigurasiKamerapelacakankerja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    nama_kamera = db.Column(db.String(100), nullable=False, unique=True)
    ip_rtsp = db.Column(db.String(255), nullable=False, unique=True)
   
    admin = relationship("Admin", back_populates="konfigurasi_kamera_pelacakan")

    def __repr__(self):
        return f"<KonfigurasiKamerapelacakankerja {self.nama_kamera})>"

# definisi tabel Superadmin 
class Superadmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='superadmin')
    photo = db.Column(db.String(255), nullable=True)  

    def __repr__(self):
        return f"<Superadmin {self.username}>"
    
# definisi tabel admin 
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_instansi = db.Column(db.Integer, nullable=False)  # ID Perusahaan
    nama_instansi = db.Column(db.String(100), nullable=False)  # Nama Perusahaan
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    model_path = db.Column(db.String(255))
    model_makanminum = db.Column(db.String(255)) # Model YOLO deteksi makan dan minum (kolom baru)
    role = db.Column(db.String(20), nullable=False, default='admin')
    photo = db.Column(db.String(255), nullable=True) 

    # Relasi 
    konfigurasi_kamera = relationship("KonfigurasiKamerapresensi", back_populates="admin", cascade="all, delete-orphan")
    konfigurasi_kamera_pelacakan = relationship("KonfigurasiKamerapelacakankerja", back_populates="admin", cascade="all, delete-orphan")
    divisi = relationship("Divisi", back_populates="admin", cascade="all, delete-orphan")
    pegawai = relationship("Pegawai", back_populates="admin", cascade="all, delete-orphan")
    absensi = db.relationship("AbsensiPegawai", back_populates="admin", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Admin {self.username} - {self.nama_instansi}>"

    
@app.route('/')
def index():
    return redirect(url_for('login'))  

# Folder penyimpanan foto
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fungsi untuk mengecek ekstensi file yang diizinkan

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session or 'role' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']
   
    

    # Ambil user berdasarkan role
    if role == 'admin':
        user = Admin.query.filter_by(id=user_id).first()
        back_url = url_for('admin_dashboard')
    elif role == 'superadmin':
        user = Superadmin.query.filter_by(id=user_id).first()
        back_url = url_for('super_admin_dashboard')
    elif role == 'pegawai':
        user = Pegawai.query.filter_by(id=user_id).first()
        back_url = url_for('pegawai_dashboard')
    else:
        return redirect(url_for('login'))

    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Hanya superadmin yang bisa ubah nama_instansi
        if role == 'superadmin':
            user.nama_instansi = request.form.get('fullname')
        elif role == 'pegawai':
            user.nama_pegawai = request.form.get('fullname')
        # Admin tidak bisa ubah nama

        # Update username & password
        user.username = request.form.get('username')
        new_password = request.form.get('password')
        if new_password:
            user.password = new_password  # Gunakan hash jika pakai bcrypt

        # Proses upload foto
        file = request.files.get('photo')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            user.photo = filename

        db.session.commit()
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(request.url)

    # Siapkan data untuk dikirim ke template
    user_data = {
        'username': user.username,
        'fullname': getattr(user, 'nama_instansi', '') or getattr(user, 'nama_pegawai', '') or '',
        'role': user.role,
        'photo': getattr(user, 'photo', None)
    }

    return render_template(
        'profile.html',
        user=user_data,
        back_url=back_url,
        username=user.username,  
        role=user.role        
    )




@app.context_processor
def inject_user_photo_only():
    if 'user_id' in session and 'role' in session:
        role = session['role']
        user_id = session['user_id']


        user = None
        if role == 'admin':
            user = Admin.query.get(user_id)
        elif role == 'superadmin':
            user = Superadmin.query.get(user_id)
        elif role == 'pegawai':
            user = Pegawai.query.get(user_id)


        return dict(user=user)


    return dict(user=None)



@app.route('/sign-in', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Ambil user dari semua role
        admin_user = Admin.query.filter_by(username=username).first()
        pegawai_user = Pegawai.query.filter_by(username=username).first()
        superadmin_user = Superadmin.query.filter_by(username=username).first()

        user = admin_user or pegawai_user or superadmin_user

        if user:
            if user.password == password:
                # Simpan session
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role

                # Tentukan target redirect
                target = 'super_admin_dashboard' if user.role == 'superadmin' \
                         else 'admin_dashboard' if user.role == 'admin' \
                         else 'pegawai_dashboard'

                # Siapkan response dan set cookie dasar
                response = make_response(redirect(url_for(target)))
                response.set_cookie('user_id', str(user.id), max_age=3600)
                response.set_cookie('username', user.username, max_age=3600)
                response.set_cookie('role', user.role, max_age=3600)

                # Tambahkan cookie khusus role
                if user.role == 'pegawai':
                    response.set_cookie('pegawai_id', str(user.id), max_age=3600)
                    if hasattr(user, 'admin_id'):
                        response.set_cookie('admin_id', str(user.admin_id), max_age=3600)
                elif user.role == 'admin':
                    response.set_cookie('admin_id', str(user.id), max_age=3600)

                    # === Load YOLO model presensi (orang) ===
                    try:
                        model_path = os.path.join(app.root_path, 'static', user.model_path)
                        print("🔍 Mencoba memuat model presensi dari:", model_path)

                        if os.path.exists(model_path):
                            model_instance = YOLO(model_path)
                            models_by_admin[int(user.id)] = model_instance
                            print("✅ Model presensi berhasil dimuat")

                            load_class_names(user.id, model_path)
                            print("✅ class_names berhasil dimuat")
                        else:
                            print(f"⚠️ Model presensi belum tersedia di: {model_path}")
                    except Exception as e:
                        print(f"❌ Gagal memuat model presensi: {e}")

                    # === Load YOLO model makan/minum ===
                    try:
                        if user.model_makanminum:
                            model_path_pelanggaran = os.path.join(app.root_path, 'static', 'models', admin_data.model_makanminum)
                            print("🔍 Mencoba memuat model makan/minum dari:", model_path_pelanggaran)

                            if os.path.exists(model_path_pelanggaran):
                                model_pelanggaran = YOLO(model_path_pelanggaran)
                                model_pelanggaran_by_admin[int(user.id)] = model_pelanggaran
                                print("✅ Model makan/minum berhasil dimuat")
                            else:
                                print(f"⚠️ Model makan/minum belum tersedia di: {model_path_pelanggaran}")
                        else:
                            print("⚠️ Kolom model_makanminum kosong di database Admin")
                    except Exception as e:
                        print(f"❌ Gagal memuat model makan/minum: {e}")

                return response
            else:
                return "Password salah!"
        else:
            return "Username tidak ditemukan!"

    return render_template('sign-in.html')





# Route Dashboard Superadmin
@app.route('/super_admin_dashboard', methods=['GET', 'POST'])
def super_admin_dashboard():
    if 'user_id' not in session or session['role'] != 'superadmin':
        return redirect(url_for('login'))  # Jika belum login atau bukan superadmin, redirect ke login

    # Ambil daftar admin
    admins = Pegawai.query.filter_by(role='admin').all()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Enkripsi password sebelum disimpan
        hashed_password = generate_password_hash(password)

        # Simpan akun admin baru ke database
        new_admin = Pegawai(username=username, password=hashed_password, role='admin')
        db.session.add(new_admin)
        db.session.commit()

        return redirect(url_for('super_admin_dashboard'))  # Redirect kembali ke halaman dashboard

    return render_template('super_admin_dashboard.html', username=session['username'], admins=admins)

# Route untuk menampilkan halaman admin
from flask import (
    render_template, request, redirect, url_for, session,
    flash
)
from sqlalchemy import or_
import os
from werkzeug.utils import secure_filename

@app.route('/super-admin/user', methods=['GET', 'POST'])
def super_admin_user():
    # Cek session login
    if 'user_id' not in session or 'role' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    # Ambil data user yang sedang login
    user = None
    if role == 'superadmin':
        user = Superadmin.query.get(user_id)
    elif role == 'admin':
        user = Admin.query.get(user_id)
    elif role == 'pegawai':
        user = Pegawai.query.get(user_id)

    if not user:
        flash('Session tidak valid. Silakan login ulang.', 'danger')
        return redirect(url_for('login'))

    # Proses POST (Add / Edit / Delete)
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            id_instansi = request.form.get('id_instansi')
            nama_instansi = request.form.get('nama_instansi')
            username = request.form.get('username')
            password = request.form.get('password')
            model_file = request.files.get('model_file')

            if not (id_instansi and nama_instansi and username and password):
                flash('Semua field harus diisi!', 'danger')
                return redirect(url_for('super_admin_user'))

            existing_user = Admin.query.filter_by(username=username).first()
            if existing_user:
                flash('Username sudah digunakan!', 'danger')
                return redirect(url_for('super_admin_user'))

            try:
                new_admin = Admin(
                    id_instansi=id_instansi,
                    nama_instansi=nama_instansi,
                    username=username,
                    password=password,
                    model_path=''
                )
                db.session.add(new_admin)
                db.session.commit()

                # Simpan model jika ada
                if model_file and model_file.filename != '':
                    model_folder = os.path.join(app.root_path, 'static', 'models')
                    os.makedirs(model_folder, exist_ok=True)

                    filename = f"{nama_instansi}_model.pt"
                    file_path = os.path.join(model_folder, filename)
                    model_file.save(file_path)

                    new_admin.model_path = f"models/{filename}"
                    db.session.commit()

                flash('Admin berhasil ditambahkan!', 'success')
                return redirect(url_for('super_admin_user'))

            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}', 'danger')
                return redirect(url_for('super_admin_user'))

        elif action == 'edit':
            admin_id = request.form.get('admin_id')
            admin = Admin.query.get(admin_id)

            if admin:
                admin.id_instansi = request.form.get('id_instansi')
                admin.nama_instansi = request.form.get('nama_instansi')
                admin.username = request.form.get('username')
                admin.password = request.form.get('password')

                model_file = request.files.get('model_file')
                if model_file and model_file.filename.endswith('.pt'):
                    model_folder = os.path.join(app.root_path, 'static', 'models')
                    os.makedirs(model_folder, exist_ok=True)

                    filename = f"{admin.nama_instansi}_model.pt"
                    file_path = os.path.join(model_folder, filename)
                    model_file.save(file_path)

                    admin.model_path = f"models/{filename}"

                try:
                    db.session.commit()
                    flash('Data admin berhasil diperbarui!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error: {str(e)}', 'danger')

        elif action == 'delete':
            admin_id = request.form.get('admin_id')
            admin = Admin.query.get(admin_id)

            if admin:
                try:
                    db.session.delete(admin)
                    db.session.commit()
                    flash('Data admin berhasil dihapus.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error: {str(e)}', 'danger')

        return redirect(url_for('super_admin_user'))

    # Proses GET (pagination + search)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)
    search_query = request.args.get('search', '').strip()

    query = Admin.query

    if search_query:
        query = query.filter(
            or_(
                Admin.id_instansi.like(f'%{search_query}%'),
                Admin.nama_instansi.like(f'%{search_query}%')
            )
        )

    pagination = query.paginate(page=page, per_page=per_page)
    admins = pagination.items

    return render_template(
        'super_admin_user.html',
        admins=admins,
        pagination=pagination,
        per_page=per_page,
        search_query=search_query,
        username=session.get('username'),
        role=session.get('role')
    )




# Route Dashboard Admin
@app.route('/divisi_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))  # Jika belum login atau bukan admin, redirect ke login
        admin_data = Admin.query.all()
    return render_template('divisi_dashboard.html', username=session['username'], role=session['role'])

# Route divisi
@app.route('/divisi_divisi', methods=['GET', 'POST'])
def divisi_divisi():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))  # Redirect jika tidak login atau bukan admin

    user_id = session['user_id']
    username = session.get('username')
    role = session.get('role')

    # Ambil filter dari query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)
    search = request.args.get('search', '', type=str)

    # Proses aksi edit atau delete
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'edit':
            divisi_id = request.form.get('divisi_id')
            nama_divisi = request.form.get('nama_divisi').strip()

            if not nama_divisi:
                flash('Nama divisi tidak boleh kosong!', 'danger')
                return redirect(url_for('divisi_divisi'))

            # Cari divisi yang ingin diedit
            divisi = Divisi.query.filter_by(id=divisi_id, admin_id=user_id).first()
            if divisi:
                divisi.nama_divisi = nama_divisi
                db.session.commit()
                flash('Divisi berhasil diperbarui!', 'success')
            else:
                flash('Divisi tidak ditemukan!', 'danger')
            return redirect(url_for('divisi_divisi'))

        elif action == 'delete':
            divisi_id = request.form.get('divisi_id')

            # Cari divisi yang ingin dihapus
            divisi = Divisi.query.filter_by(id=divisi_id, admin_id=user_id).first()
            if divisi:
                db.session.delete(divisi)
                db.session.commit()
                flash('Divisi berhasil dihapus!', 'success')
            else:
                flash('Divisi tidak ditemukan!', 'danger')

            return redirect(url_for('divisi_divisi'))

    # Query dasar
    query = Divisi.query.filter_by(admin_id=user_id)

    # Jika ada pencarian
    if search:
        query = query.filter(Divisi.nama_divisi.ilike(f"%{search}%"))

    divisi_list = query.order_by(Divisi.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    total_divisi = query.count()
    total_pages = divisi_list.pages
    current_page = divisi_list.page
    start = (current_page - 1) * per_page + 1
    end = start + len(divisi_list.items) - 1

    return render_template('divisi_divisi.html', 
                           username=session['username'], 
                           divisi_list=divisi_list, 
                           total_divisi=total_divisi,
                           total_pages=total_pages,
                           current_page=current_page,
                           start=start,
                           end=end,
                           search=search,
                           per_page=per_page,
                           role=role)

#route tambah divisi
@app.route('/add_divisi', methods=['POST'])
def add_divisi():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))  # Redirect jika tidak login atau bukan admin

    # Ambil user_id dari session
    user_id = session['user_id']

    nama_divisi = request.form.get('nama_divisi', '').strip()

    if not nama_divisi:
        flash('Nama divisi tidak boleh kosong!', 'danger')
        return redirect(url_for('divisi_divisi'))

    # Cek apakah divisi sudah ada untuk user_id yang sama
    existing_divisi = Divisi.query.filter_by(nama_divisi=nama_divisi, admin_id=user_id).first()
    if existing_divisi:
        flash(f'Divisi "{nama_divisi}" sudah ada!', 'warning')
    else:
        # Tambahkan divisi ke database dengan user_id
        new_divisi = Divisi(nama_divisi=nama_divisi, admin_id=user_id)
        db.session.add(new_divisi)
        db.session.commit()
        flash(f'Divisi "{nama_divisi}" berhasil ditambahkan!', 'success')

    return redirect(url_for('divisi_divisi'))


@app.route('/divisi_pegawai', methods=['GET', 'POST'])
def divisi_pegawai():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    # === HANDLE POST ===
    if request.method == 'POST':
        action = request.form.get('action')
        pegawai_id = request.form.get('pegawai_id')

        if action == 'edit':
            nama = request.form.get('nama')
            nomor = request.form.get('nomor')
            username_form = request.form.get('username')
            password = request.form.get('password')

            pegawai = Pegawai.query.get(pegawai_id)
            if pegawai:
                pegawai.nama_pegawai = nama
                pegawai.nomor_pegawai = nomor
                pegawai.username = username_form
                if password:
                    pegawai.password = password
                db.session.commit()
                flash('Data pegawai berhasil diperbarui!', 'success')

        elif action == 'delete':
            pegawai = Pegawai.query.get(pegawai_id)
            if pegawai:
                db.session.delete(pegawai)
                db.session.commit()
                flash('Pegawai berhasil dihapus!', 'danger')

        return redirect(url_for('divisi_pegawai'))

    # === HANDLE GET ===
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)
    search = request.args.get('search', '', type=str)
    selected_divisi = request.args.get('divisi', '', type=str)

    query = Pegawai.query.filter_by(admin_id=session['user_id'])

    if search:
        query = query.filter(
            Pegawai.id.ilike(f'%{search}%') |
            Pegawai.nama_pegawai.ilike(f'%{search}%') |
            Pegawai.nomor_pegawai.ilike(f'%{search}%') |
            Pegawai.divisi.has(Divisi.nama_divisi.ilike(f'%{search}%')) |
            Pegawai.username.ilike(f'%{search}%')
        )

    if selected_divisi:
        query = query.filter(Pegawai.divisi.has(Divisi.nama_divisi == selected_divisi))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    pegawai_list = pagination.items

    start_entry = (pagination.page - 1) * pagination.per_page + 1
    end_entry = min(pagination.page * pagination.per_page, pagination.total)

    divisi_list = Divisi.query.filter_by(admin_id=session['user_id']).all()
    username = session.get('username')
    role = session.get('role')

    return render_template(
        'divisi_pegawai.html',
        divisi_list=divisi_list,
        pegawai_list=pegawai_list,
        pagination=pagination,
        page=page,
        per_page=per_page,
        search=search,
        selected_divisi=selected_divisi,
        start_entry=start_entry,
        end_entry=end_entry,
        username=username,
        role=role
    )



@app.route('/import-pegawai', methods=['POST'])
def import_pegawai():
    file = request.files.get('file')

    # Ambil admin_id dari cookie
    admin_id = request.cookies.get('user_id')
    if not admin_id:
        flash("Gagal mengambil admin_id dari cookies. Silakan login ulang.", "danger")
        return redirect(url_for('divisi_pegawai'))

    try:
        admin_id = int(admin_id)
    except ValueError:
        flash("ID admin tidak valid.", "danger")
        return redirect(url_for('divisi_pegawai'))

    if not file or not file.filename.endswith('.xlsx'):
        flash("File harus format .xlsx", "danger")
        return redirect(url_for('divisi_pegawai'))

    try:
        # Pastikan nomor_pegawai dibaca sebagai string agar '+' tidak hilang
        df = pd.read_excel(file, dtype={'nomor_pegawai': str})
        df.columns = df.columns.str.strip().str.lower()  # Standarisasi kolom
    except Exception as e:
        flash(f"Gagal membaca file Excel: {str(e)}", "danger")
        return redirect(url_for('divisi_pegawai'))

    required_columns = ['nama_pegawai', 'nomor_pegawai', 'divisi', 'username', 'password']
    if not all(col in df.columns for col in required_columns):
        flash("Kolom tidak sesuai. Kolom wajib: " + ", ".join(required_columns), "danger")
        return redirect(url_for('divisi_pegawai'))

    imported_count = 0
    for _, row in df.iterrows():
        divisi_nama = str(row['divisi']).strip()

        divisi = Divisi.query.filter_by(nama_divisi=divisi_nama).first()
        if not divisi:
            divisi = Divisi(nama_divisi=divisi_nama)
            db.session.add(divisi)
            db.session.flush()  # agar dapat divisi.id

        # Cek apakah username sudah ada
        if Pegawai.query.filter_by(username=row['username']).first():
            continue

        pegawai = Pegawai(
            admin_id=admin_id,
            nama_pegawai=str(row['nama_pegawai']).strip(),
           nomor_pegawai=str(row['nomor_pegawai']).strip().lstrip("'"),
            divisi_id=divisi.id,
            username=str(row['username']).strip(),
            password=row['password'],  # Tidak di-hash
            role='pegawai'
        )
        db.session.add(pegawai)
        imported_count += 1

    try:
        db.session.commit()
        flash(f"Berhasil mengimpor {imported_count} pegawai.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menyimpan data: {str(e)}", "danger")

    return redirect(url_for('divisi_pegawai'))



# route tambah_pegawai
@app.route('/tambah_pegawai', methods=['GET', 'POST'])
def tambah_pegawai():
    if request.method == 'POST':
        # Ambil data dari form
        nama_pegawai = request.form['nama_pegawai']
        divisi_id = request.form['divisi_id']
        username = request.form['username']
        nomor_pegawai = request.form['nomor_pegawai']
        password = request.form['password']

        # Ambil admin_id dari sesi yang sedang aktif
        admin_id = session.get('user_id')  

        # Simpan data pegawai baru dengan admin_id yang sesuai
        pegawai = Pegawai(
            nama_pegawai=nama_pegawai,
            divisi_id=divisi_id,
            username=username,
            nomor_pegawai=nomor_pegawai,
            password=password,
            admin_id=admin_id 
        )
        db.session.add(pegawai)
        db.session.commit()

        return redirect(url_for('divisi_pegawai'))  # Redirect ke halaman yang diinginkan

    # Ambil data divisi dari database
    divisi_list = Divisi.query.all()

    # Debugging: print divisi_list untuk memastikan ada data
    print("Divisi List:", divisi_list)  # Pastikan ini mencetak daftar divisi

    return render_template('tambah_pegawai.html', divisi_list=divisi_list)


# Route Divisi_presentasi_pegawai
@app.route('/presensi_pegawai')
def presensi_pegawai():
    return render_template('divisi_presensi_pegawai.html') 

# Route Divisi_konfigurasi_kamera_presensi
@app.route('/divisi_kamera_presensi', methods=['GET', 'POST'])
def divisi_kamera_presensi():
    # Ambil data dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    username = request.cookies.get('username')

    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    # Proses form tambah kamera
    if request.method == 'POST':
        try:
            nama_kamera = request.form.get('nama_kamera')
            role_kamera = request.form.get('role_kamera').lower()
            ip_rtsp = request.form.get('ip_rtsp')
            jam_mulai_kedatangan = request.form.get('jam_mulai_kedatangan')
            jam_berakhir_kedatangan = request.form.get('jam_berakhir_kedatangan')
            jam_mulai_pulang = request.form.get('jam_mulai_pulang')
            jam_berakhir_pulang = request.form.get('jam_berakhir_pulang')

            if role_kamera not in ['in', 'out']:
                flash("Role Kamera harus 'in' atau 'out'", "danger")
                return redirect(url_for('divisi_kamera_presensi'))

            # Konversi jam
            jam_mulai_kedatangan = datetime.strptime(jam_mulai_kedatangan, "%H:%M").time()
            jam_berakhir_kedatangan = datetime.strptime(jam_berakhir_kedatangan, "%H:%M").time()
            jam_mulai_pulang = datetime.strptime(jam_mulai_pulang, "%H:%M").time()
            jam_berakhir_pulang = datetime.strptime(jam_berakhir_pulang, "%H:%M").time()

            kamera_baru = KonfigurasiKamerapresensi(
                admin_id=user_id,
                nama_kamera=nama_kamera,
                role_kamera=RoleKamera(role_kamera),
                ip_rtsp=ip_rtsp,
                jam_mulai_kedatangan=jam_mulai_kedatangan,
                jam_berakhir_kedatangan=jam_berakhir_kedatangan,
                jam_mulai_pulang=jam_mulai_pulang,
                jam_berakhir_pulang=jam_berakhir_pulang
            )
            db.session.add(kamera_baru)
            db.session.commit()
            flash("Kamera Presensi berhasil ditambahkan!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('divisi_kamera_presensi'))

    # Ambil filter dari query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)
    search = request.args.get('search', '', type=str)

    # Query dasar
    query = KonfigurasiKamerapresensi.query.filter_by(admin_id=user_id)

    # Filter pencarian
    if search:
        query = query.filter(KonfigurasiKamerapresensi.nama_kamera.ilike(f"%{search}%"))

    # Paginate hasil
    pagination = query.order_by(KonfigurasiKamerapresensi.id.desc()).paginate(page=page, per_page=per_page)
    kamera_list = pagination.items

    return render_template('divisi_kamera_presensi.html',
                           kamera_list=kamera_list,
                           pagination=pagination,
                           search=search,
                           per_page=per_page,
                           username=username,
                           role=role)


# Route edit konfigurasi kamera presensi
@app.route('/edit_kamera/<int:kamera_id>', methods=['GET', 'POST'])
def edit_kamera(kamera_id):
    # Ambil data admin_id dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')

    # Jika tidak ada user_id di cookies atau role bukan admin, redirect ke halaman login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    # Ambil data kamera berdasarkan kamera_id
    kamera = KonfigurasiKamerapresensi.query.get(kamera_id)
    if kamera:
        # Periksa apakah admin_id pada kamera sesuai dengan user_id di cookies
        if kamera.admin_id != int(user_id):
            flash("Anda tidak memiliki izin untuk mengedit kamera ini.", "danger")
            return redirect(url_for('divisi_kamera_presensi'))

        if request.method == 'POST':
            # Update data kamera sesuai dengan input form
            kamera.nama_kamera = request.form['nama_kamera']
            kamera.ip_rtsp = request.form['ip_rtsp']
            kamera.jam_mulai_kedatangan = request.form['jam_mulai_kedatangan']
            kamera.jam_berakhir_kedatangan = request.form['jam_berakhir_kedatangan']
            kamera.jam_mulai_pulang = request.form['jam_mulai_pulang']
            kamera.jam_berakhir_pulang = request.form['jam_berakhir_pulang']
            db.session.commit()
            flash("Kamera berhasil diperbarui!", "success")

    return redirect(url_for('divisi_kamera_presensi'))


# Route delete konfigurasi kamera presensi
@app.route('/hapus_kamera/<int:kamera_id>', methods=['POST'])
def hapus_kamera(kamera_id):
    # Ambil data admin_id dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')

    # Jika tidak ada user_id di cookies atau role bukan admin, redirect ke halaman login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    try:
        # Ambil kamera berdasarkan kamera_id
        kamera = KonfigurasiKamerapresensi.query.get(kamera_id)
        if not kamera:
            flash("Kamera tidak ditemukan!", "danger")
            return redirect(url_for('divisi_kamera_presensi'))

        # Periksa apakah admin_id pada kamera sesuai dengan user_id di cookies
        if kamera.admin_id != int(user_id):
            flash("Anda tidak memiliki izin untuk menghapus kamera ini.", "danger")
            return redirect(url_for('divisi_kamera_presensi'))

        # Hapus kamera dari database
        db.session.delete(kamera)
        db.session.commit()
        flash("Kamera berhasil dihapus!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('divisi_kamera_presensi'))


# Route Divisi_konfigurasi_kamera pelacakan kinerja
@app.route('/divisi_kamera_pelacakan', methods=['GET', 'POST'])
def divisi_kamera_pelacakan():
    # Ambil data admin_id dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    username = request.cookies.get('username')

    # Jika tidak ada user_id di cookies atau role bukan admin, redirect ke halaman login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            nama_kamera = request.form.get('nama_kamera')
            ip_rtsp = request.form.get('ip_rtsp')

            if not nama_kamera or not ip_rtsp:
                flash("Nama Kamera dan IP RTSP harus diisi!", "danger")
                return redirect(url_for('divisi_kamera_pelacakan'))

            # Menambahkan kamera pelacakan baru ke database
            kamera_baru = KonfigurasiKamerapelacakankerja(
                nama_kamera=nama_kamera,
                ip_rtsp=ip_rtsp,
                admin_id=int(user_id)  # Pastikan admin_id diisi dengan ID admin yang login
            )
            db.session.add(kamera_baru)
            db.session.commit()
            flash("Kamera Pelacakan berhasil ditambahkan!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('divisi_kamera_pelacakan'))

    kamerapelacakan_list = KonfigurasiKamerapelacakankerja.query.all()
    return render_template('divisi_kamera_pelacakan.html', kamerapelacakan_list=kamerapelacakan_list, username=username, role=role)



# Route edit konfigurasi kamera pelacakan
@app.route('/edit_kamerapelacakan/<int:kamera_id>', methods=['POST'])
def edit_kamerapelacakan(kamera_id):
    # Ambil data admin_id dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')

    # Jika tidak ada user_id di cookies atau role bukan admin, redirect ke halaman login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    # Ambil data kamera berdasarkan kamera_id
    kamera = KonfigurasiKamerapelacakankerja.query.get(kamera_id)
    if kamera:
        # Periksa apakah admin_id pada kamera sesuai dengan user_id di cookies
        if kamera.admin_id != int(user_id):
            flash("Anda tidak memiliki izin untuk mengedit kamera ini.", "danger")
            return redirect(url_for('divisi_kamera_pelacakan'))

        if request.method == 'POST':
            # Update data kamera pelacakan sesuai dengan input form
            kamera.nama_kamera = request.form['nama_kamera']
            kamera.ip_rtsp = request.form['ip_rtsp']
            db.session.commit()
            flash("Kamera pelacakan berhasil diperbarui!", "success")

    return redirect(url_for('divisi_kamera_pelacakan'))


# Route delete konfigurasi kamera pelacakan
@app.route('/hapus_kamerapelacakan/<int:kamera_id>', methods=['POST'])
def hapus_kamerapelacakan(kamera_id):
    # Ambil data admin_id dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')


    # Jika tidak ada user_id di cookies atau role bukan admin, redirect ke halaman login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))


    try:
        # Ambil kamera berdasarkan kamera_id
        kamera = KonfigurasiKamerapelacakankerja.query.get(kamera_id)
        if not kamera:
            flash("Kamera tidak ditemukan!", "danger")
            return redirect(url_for('divisi_kamera_pelacakan'))


        # Periksa apakah admin_id pada kamera sesuai dengan user_id di cookies
        if kamera.admin_id != int(user_id):
            flash("Anda tidak memiliki izin untuk menghapus kamera ini.", "danger")
            return redirect(url_for('divisi_kamera_pelacakan'))
        # Hapus kamera dari database
        db.session.delete(kamera)
        db.session.commit()
        flash("Kamera berhasil dihapus!", "success")


    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('divisi_kamera_pelacakan'))




@app.route('/pegawai_dashboard')
def pegawai_dashboard():
    if 'user_id' not in session or session['role'] != 'pegawai':
        return redirect(url_for('login'))  # Jika belum login atau bukan pegawai, redirect ke login
        pegawai_data = Pegawai.query.all()
    return render_template('pegawai_dashboard.html', username=session['username'], role=session['role'])

# Route Absensi Pegawai
@app.route('/pegawai_absensi')
def pegawai_absensi():
    if 'username' not in session or 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']
    role = session['role']

    pegawai = Pegawai.query.get(user_id)
    if not pegawai:
        flash("Pegawai tidak ditemukan.", "danger")
        return redirect(url_for('login'))

    tanggal_filter = request.args.get('tanggal')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Set the number of entries per page

    query = AbsensiPegawai.query.filter_by(pegawai_id=pegawai.id)

    if tanggal_filter:
        try:
            tanggal_obj = datetime.strptime(tanggal_filter, '%Y-%m-%d').date()
            query = query.filter(AbsensiPegawai.tanggal == tanggal_obj)
        except ValueError:
            flash("Format tanggal tidak valid.", "danger")

    # Paginate the query
    absensi_paginated = query.order_by(AbsensiPegawai.tanggal.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('pegawai_absensi.html', username=username, role=role, absensi=absensi_paginated)

# Route Lama Kerja Pegawai
@app.route('/pegawai_lamakerja')
def pegawai_lamakerja():
    if 'username' not in session or 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']
    role = session['role']

    pegawai = Pegawai.query.get(user_id)
    if not pegawai:
        flash("Pegawai tidak ditemukan.", "danger")
        return redirect(url_for('login'))

    tanggal_filter = request.args.get('tanggal')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Jumlah data per halaman

    query = LamaKerja.query.filter_by(pegawai_id=pegawai.id)

    if tanggal_filter:
        try:
            tanggal_obj = datetime.strptime(tanggal_filter, '%Y-%m-%d').date()
            query = query.filter(LamaKerja.tanggal == tanggal_obj)
        except ValueError:
            flash("Format tanggal tidak valid.", "danger")

    lama_kerja_paginated = query.order_by(LamaKerja.tanggal.desc()).paginate(page=page, per_page=per_page, error_out=False)

    for row in lama_kerja_paginated.items:
        # Proses URL gambar jika ada
        foto_bukti_nama = row.foto_bukti.replace('\\', '/').split('static/')[-1] if row.foto_bukti else None
        row.foto_bukti_url = url_for('static', filename=foto_bukti_nama) if foto_bukti_nama else None

        foto_pelanggaran_nama = row.foto_pelanggaran.replace('\\', '/').split('static/')[-1] if row.foto_pelanggaran else None
        row.foto_pelanggaran_url = url_for('static', filename=foto_pelanggaran_nama) if foto_pelanggaran_nama else None

    return render_template(
        'pegawai_lamakerja.html',
        lama_kerja_data=lama_kerja_paginated,
        username=username,
        role=role,
        tanggal=tanggal_filter
    )


#Route Kamera Presensi
@app.route('/admin_kamera_presensi_realtime')
def admin_kamera_presensi_realtime():
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    username = request.cookies.get('username')

    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    #  Cek apakah model sudah dimuat untuk admin
    if int(user_id) not in models_by_admin:
        flash("Model belum tersedia. Silakan upload model terlebih dahulu.", "warning")
        return redirect(url_for('admin_dashboard'))

    konfigurasi_kamera = KonfigurasiKamerapresensi.query.filter_by(admin_id=user_id).all()

    if not konfigurasi_kamera:
        flash('Silakan tambahkan IP RTSP di konfigurasi presensi.', 'warning')
        return redirect(url_for('divisi_kamera_presensi'))

    valid_rtsp_presensi = [kamera.ip_rtsp for kamera in konfigurasi_kamera if kamera.ip_rtsp]

    if not valid_rtsp_presensi:
        flash('Silakan tambahkan IP RTSP di konfigurasi presensi.', 'warning')
        return redirect(url_for('divisi_kamera_presensi'))

    return render_template('admin_kamera_presensi_realtime.html',
                           num_cameras=len(valid_rtsp_presensi),
                           username=session['username'],
                           role=session['role'])


#Route Kamera Pelacakan Kinerja
@app.route('/admin_kamera_pelacakan_realtime')
def admin_kamera_pelacakan_realtime():
    # Ambil data dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')
    username = request.cookies.get('username')

    # Jika tidak ada user_id di cookies atau role bukan admin, redirect ke halaman login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    # Ambil admin_id dari cookies
    admin_id = user_id  # Asumsi user_id di cookies adalah admin_id

    # Cek apakah ada konfigurasi kamera pelacakan kinerja untuk admin yang sedang login
    konfigurasi_kamera = KonfigurasiKamerapelacakankerja.query.filter_by(admin_id=admin_id).all()

    # Jika tidak ada konfigurasi kamera, tampilkan pesan dan redirect
    if not konfigurasi_kamera:
        flash('Silakan tambahkan IP RTSP di konfigurasi pelacakan kinerja.', 'warning')
        return redirect(url_for('divisi_kamera_pelacakan'))

    # Filter hanya kamera dengan IP RTSP yang valid
    kamera_valid = [kamera for kamera in konfigurasi_kamera if kamera.ip_rtsp]

    # Jika tidak ada RTSP yang valid, beri pesan
    if not kamera_valid:
        flash('Silakan tambahkan IP RTSP di konfigurasi pelacakan kinerja.', 'warning')
        return redirect(url_for('divisi_kamera_pelacakan'))

    # Kirim list kamera valid (bukan hanya IP), agar bisa akses nama_kamera juga di template
    return render_template(
        'admin_kamera_pelacakan_realtime.html',
        cameras=kamera_valid,  # Ini sekarang list objek kamera, bukan list IP
        username=username,
        role=role
    )



#Route Presensi Pegawai
@app.route('/admin_kamera_presensi', methods=['GET', 'POST'])
def admin_kamera_presensi():
    admin_id = request.cookies.get('user_id') or session.get('user_id')
    role = request.cookies.get('role') or session.get('role')
    username = request.cookies.get('username') or session.get('username')

    if not admin_id:
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "danger")
        return redirect(url_for('login'))

    # Ambil daftar pegawai
    pegawai_tercatat = db.session.query(Pegawai.id, Pegawai.nama_pegawai).distinct().all()

    # Ambil parameter filter
    tanggal = request.args.get('tanggal')
    pegawai_id = request.args.get('pegawai')
    jam_lembur = request.args.get('jam_lembur')
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Mulai query
    query = db.session.query(AbsensiPegawai).join(Pegawai).join(Divisi).filter(
    AbsensiPegawai.admin_id == admin_id
)


    if tanggal:
        query = query.filter(AbsensiPegawai.tanggal == tanggal)
    if pegawai_id:
        query = query.filter(AbsensiPegawai.pegawai_id == pegawai_id)
    if jam_lembur:
        query = query.filter(AbsensiPegawai.jam_lembur == jam_lembur)

    # Tambahkan fitur pencarian
    if search_query:
        query = query.filter(
        or_(
            Pegawai.id.ilike(f"%{search_query}%"),
            Pegawai.nama_pegawai.ilike(f"%{search_query}%"),
            Divisi.nama_divisi.ilike(f"%{search_query}%"),
            AbsensiPegawai.tanggal.ilike(f"%{search_query}%")
        )
    )



    if request.method == 'POST':
        action = request.form.get('action')

        # Proses Edit Data
        if action == 'edit':
            pegawai_id = request.form.get('pegawai_id')
            nama = request.form.get('nama')
            tanggal = request.form.get('tanggal')
            presensi_datang = request.form.get('presensi_datang')
            status = request.form.get('status')
            presensi_pulang = request.form.get('presensi_pulang')
            jam_kerja = request.form.get('jam_kerja')
            jam_lembur = request.form.get('jam_lembur')

            absensi = AbsensiPegawai.query.filter_by(
                pegawai_id=pegawai_id, admin_id=admin_id, tanggal=tanggal
            ).first()

            if absensi:
                absensi.nama_pegawai = nama
                absensi.tanggal = tanggal
                absensi.presensi_datang = presensi_datang
                absensi.status = status
                absensi.presensi_pulang = presensi_pulang
                absensi.jam_kerja = jam_kerja
                absensi.jam_lembur = jam_lembur
                db.session.commit()
                flash("Data berhasil diperbarui!", "success")
            else:
                flash("Data absensi tidak ditemukan!", "danger")

        # Proses Hapus Data
        elif action == 'delete':
            pegawai_id = request.form.get('pegawai_id')
            tanggal = request.form.get('tanggal')

            if not pegawai_id or not tanggal:
                flash("ID Pegawai atau Tanggal tidak ditemukan!", "danger")
                return redirect(url_for('admin_kamera_presensi'))

            deleted_rows = AbsensiPegawai.query.filter_by(
                pegawai_id=pegawai_id, tanggal=tanggal, admin_id=admin_id
            ).delete()

            if deleted_rows == 0:
                flash("Data tidak ditemukan!", "warning")
            else:
                db.session.commit()
                flash("Data berhasil dihapus!", "success")

            return redirect(url_for('admin_kamera_presensi'))

    # Ambil data sesuai dengan pagination
    absensi_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'admin_presensi_pegawai.html', 
        absensi_data=absensi_paginated, 
        pegawai_tercatat=pegawai_tercatat,
        username=username,
        role=role
    )



# Route export presensi pegawai pdf
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Laporan Presensi Pegawai", ln=True, align="C")
        self.ln(5)

@app.route('/export-presensi', methods=['GET'])
def export_presensi():
    tanggal_mulai = request.args.get('tanggal_mulai')
    tanggal_selesai = request.args.get('tanggal_selesai')
    pegawai_id = request.args.get('pegawai_id')
    
    # Validasi input
    try:
        start_date = datetime.strptime(tanggal_mulai, '%Y-%m-%d').date()
        end_date = datetime.strptime(tanggal_selesai, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return "Tanggal tidak valid", 400

    query = AbsensiPegawai.query.filter(AbsensiPegawai.tanggal.between(start_date, end_date))
    if pegawai_id:
        query = query.filter(AbsensiPegawai.pegawai_id == int(pegawai_id))
    
    absensi_data = query.order_by(AbsensiPegawai.tanggal.asc()).all()
    
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    col_widths = [10, 15, 35, 30, 25, 25, 15, 30, 25, 15, 25, 25]
    pdf.set_fill_color(200, 220, 255)
    
    headers = ["No", "ID", "Nama", "Divisi", "Tanggal", "Datang", "Foto", "Status", "Pulang", "Foto", "Jam Kerja", "Lembur"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
    pdf.ln()
    
    for index, absensi in enumerate(absensi_data, start=1):
        pdf.cell(col_widths[0], 10, str(index), 1, 0, 'C')
        pdf.cell(col_widths[1], 10, str(absensi.pegawai.id), 1)
        pdf.cell(col_widths[2], 10, absensi.pegawai.nama_pegawai[:15], 1)
        pdf.cell(col_widths[3], 10, absensi.pegawai.divisi.nama_divisi[:10], 1)
        pdf.cell(col_widths[4], 10, absensi.tanggal.strftime('%d-%m-%Y'), 1)
        pdf.cell(col_widths[5], 10, str(absensi.presensi_datang), 1)
        
        foto_datang_path = os.path.join("static", absensi.foto_datang) if absensi.foto_datang else None
        if foto_datang_path and os.path.exists(foto_datang_path):
            pdf.image(foto_datang_path, x=pdf.get_x(), y=pdf.get_y(), w=10, h=10)
            pdf.cell(col_widths[6], 10, "", 1)
        else:
            pdf.cell(col_widths[6], 10, "-", 1)
        
        status = "Belum Pulang" if absensi.presensi_datang and not absensi.presensi_pulang else ("Pulang" if absensi.presensi_pulang else "Tidak Hadir")
        pdf.cell(col_widths[7], 10, status, 1)
        pdf.cell(col_widths[8], 10, str(absensi.presensi_pulang) if absensi.presensi_pulang else "-", 1)
        
        foto_pulang_path = os.path.join("static", absensi.foto_pulang) if absensi.foto_pulang else None
        if foto_pulang_path and os.path.exists(foto_pulang_path):
            pdf.image(foto_pulang_path, x=pdf.get_x(), y=pdf.get_y(), w=10, h=10)
            pdf.cell(col_widths[9], 10, "", 1)
        else:
            pdf.cell(col_widths[9], 10, "-", 1)
        
        pdf.cell(col_widths[10], 10, str(absensi.jam_kerja), 1)
        pdf.cell(col_widths[11], 10, str(absensi.jam_lembur) if absensi.jam_lembur else "-", 1)
        pdf.ln()
    
    pdf_file = "laporan_presensi.pdf"
    pdf.output(pdf_file)
    
    return send_file(pdf_file, as_attachment=True)

#Route Kamera Lama Kerja
@app.route('/admin_lama_kerja', methods=['GET', 'POST'])
def admin_lama_kerja():
    admin_id = request.cookies.get('user_id')

    if not admin_id:
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "danger")
        return redirect(url_for('login'))

    username = session.get('username')
    role = session.get('role')

    # Proses form edit
    if request.method == 'POST' and request.form.get('edit_id'):
        edit_id = int(request.form['edit_id'])
        lama_kerja = LamaKerja.query.get(edit_id)
        if lama_kerja:
            lama_kerja.tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d').date()
            lama_kerja.nama_pegawai = request.form['nama_pegawai']
            lama_kerja.divisi = request.form['divisi']
            lama_kerja.lama_terdeteksi = int(request.form['lama_terdeteksi'])
            lama_kerja.area_cctv = request.form['area_cctv']

            foto_file = request.files.get('foto_bukti')
            if foto_file and foto_file.filename != '':
                lama_kerja.foto_bukti = foto_file.read()

            db.session.commit()
            flash("Data berhasil diperbarui.", "success")
        return redirect(url_for('admin_lama_kerja'))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if per_page < 1:
        per_page = 10

    tanggal = request.args.get('tanggal', None)
    pegawai_id = request.args.get('pegawai', None)
    search = request.args.get('search', '').strip()

    query = LamaKerja.query.filter_by(admin_id=admin_id)

    if tanggal:
        try:
            tanggal_obj = datetime.strptime(tanggal, "%Y-%m-%d").date()
            query = query.filter(LamaKerja.tanggal == tanggal_obj)
        except ValueError:
            flash("Format tanggal tidak valid.", "danger")

    if pegawai_id:
        query = query.filter(LamaKerja.pegawai_id == pegawai_id)

    if search:
        query = query.filter(or_(
            LamaKerja.nama_pegawai.ilike(f"%{search}%"),
            LamaKerja.divisi.ilike(f"%{search}%"),
            LamaKerja.area_cctv.ilike(f"%{search}%"),
            LamaKerja.tanggal.cast(String).ilike(f"%{search}%"),
            LamaKerja.lama_terdeteksi.cast(String).ilike(f"%{search}%")
        ))

    lama_kerja_data = query.paginate(page=page, per_page=per_page, error_out=False)

    for row in lama_kerja_data.items:
        foto_bukti_nama = row.foto_bukti.replace('\\', '/').split('static/')[-1] if row.foto_bukti else None
        row.foto_bukti_url = url_for('static', filename=foto_bukti_nama) if foto_bukti_nama else None

        foto_pelanggaran_nama = row.foto_pelanggaran.replace('\\', '/').split('static/')[-1] if row.foto_pelanggaran else None
        row.foto_pelanggaran_url = url_for('static', filename=foto_pelanggaran_nama) if foto_pelanggaran_nama else None

    pegawai_data = Pegawai.query.all()

    return render_template(
        'admin_lama_kerja.html',
        lama_kerja_data=lama_kerja_data,
        pegawai_data=pegawai_data,
        page=page,
        per_page=per_page,
        tanggal=tanggal,
        pegawai_id=pegawai_id,
        search=search,
        username=username,
        role=role
    )


@app.template_filter('format_durasi')
def format_durasi(detik):
    if not detik:
        return "0 Detik"
    jam = detik // 3600
    menit = (detik % 3600) // 60
    detik_sisa = detik % 60
    return f"{jam} Jam {menit} Menit {detik_sisa} Detik"



#Route Edit Lama Kerja
@app.route('/edit_lama_kerja/<int:id>', methods=['GET', 'POST'])
def edit_lama_kerja(id):
    lama_kerja = LamaKerja.query.get_or_404(id)

    if request.method == 'POST':
        lama_kerja.tanggal = datetime.strptime(request.form['tanggal'], '%Y-%m-%d').date()
        lama_kerja.nama_pegawai = request.form['nama_pegawai']
        lama_kerja.divisi = request.form['divisi']
        lama_kerja.lama_terdeteksi = int(request.form['lama_terdeteksi'])
        lama_kerja.area_cctv = request.form['area_cctv']

        foto_file = request.files.get('foto_bukti')
        if foto_file and foto_file.filename != '':
            lama_kerja.foto_bukti = foto_file.read()

        db.session.commit()
        flash('Data berhasil diperbarui.', 'success')
        return redirect(url_for('admin_lama_kerja'))

    return render_template('edit_lama_kerja.html', lama_kerja=lama_kerja)

#Route Hapus Data Lama Kerja    
# Route untuk menghapus data lama kerja
@app.route('/hapus_lamakerja/<int:lama_kerja_id>', methods=['POST'])
def hapus_lamakerja(lama_kerja_id):
    # Ambil data user dari cookies
    user_id = request.cookies.get('user_id')
    role = request.cookies.get('role')

    # Validasi role dan login
    if not user_id or role != 'admin':
        flash("Anda tidak memiliki akses untuk halaman ini.", "danger")
        return redirect(url_for('login'))

    try:
        # Cari data berdasarkan ID
        data = LamaKerja.query.get(lama_kerja_id)
        if not data:
            flash("Data tidak ditemukan!", "danger")
            return redirect(url_for('admin_lama_kerja'))

        # Validasi kepemilikan data
        if data.admin_id != int(user_id):
            flash("Anda tidak memiliki izin untuk menghapus data ini.", "danger")
            return redirect(url_for('admin_lama_kerja'))

        # Hapus data
        db.session.delete(data)
        db.session.commit()
        flash("Data berhasil dihapus!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Terjadi kesalahan: {str(e)}", "danger")

    return redirect(url_for('admin_lama_kerja'))


#Route Log Out
@app.route('/logout')
def logout():
    user_id = session.get('user_id')

    # Hapus data model jika ada
    if user_id and int(user_id) in models_by_admin:
        del models_by_admin[int(user_id)]
        print(f"🧹 Model admin dengan ID {user_id} telah dibersihkan dari cache.")

    # Bersihkan session dan cookies
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('user_id')
    response.delete_cookie('username')
    response.delete_cookie('role')
    response.delete_cookie('pegawai_id')

    return response

 


@app.route('/api/chart-data')
def chart_data():
    admin_id = request.cookies.get('user_id')
    if not admin_id:
        return jsonify({"error": "Unauthorized"}), 401

    print(f"admin_id: {admin_id}")  # Log admin_id

    konfigurasi = KonfigurasiKamerapresensi.query.filter_by(admin_id=admin_id).first()
    if not konfigurasi:
        return jsonify({"error": "Konfigurasi kamera tidak ditemukan"}), 404

    # print(f"Konfigurasi ditemukan: {konfigurasi}")  # Log konfigurasi

    jam_toleransi_datang = konfigurasi.jam_berakhir_kedatangan
    jam_toleransi_pulang = konfigurasi.jam_mulai_pulang

    data = db.session.query(
        func.date_format(AbsensiPegawai.tanggal, '%Y-%m-01').label('bulan'),
        AbsensiPegawai.pegawai_id,
        AbsensiPegawai.presensi_datang,
        AbsensiPegawai.presensi_pulang
    ).filter(
        AbsensiPegawai.admin_id == admin_id
    ).all()

    # print(f"Data yang diambil: {data}")  # Log data yang diambil

    hasil = {}
    for row in data:
        bulan_str = row.bulan

        if bulan_str not in hasil:
            hasil[bulan_str] = {"tepat_waktu": set(), "telat": set(), "lembur": set()}

        # Hitung datang
        if row.presensi_datang:
            if row.presensi_datang <= jam_toleransi_datang:
                hasil[bulan_str]["tepat_waktu"].add(row.pegawai_id)
            else:
                hasil[bulan_str]["telat"].add(row.pegawai_id)

        # Hitung lembur
        if row.presensi_pulang and row.presensi_pulang > jam_toleransi_pulang:
            hasil[bulan_str]["lembur"].add(row.pegawai_id)

    labels = list(hasil.keys())
    series = [
        {"name": "Tepat Waktu", "data": [len(hasil[b]["tepat_waktu"]) for b in labels]},
        {"name": "Telat", "data": [len(hasil[b]["telat"]) for b in labels]},
        {"name": "Lembur", "data": [len(hasil[b]["lembur"]) for b in labels]},
    ]

    # print(f"Labels: {labels}, Series: {series}")  # Log data series

    return jsonify({"labels": labels, "series": series})

@app.route('/top-pegawai', methods=['GET'])
def top_pegawai():
    bulan = request.args.get('bulan', default=datetime.now().month, type=int)
    tahun = request.args.get('tahun', default=datetime.now().year, type=int)
    filter_ = request.args.get('filter', default='ontime', type=str)

    try:
        bulan = int(bulan)
        tahun = int(tahun)
    except ValueError:
        return jsonify({"error": "Bulan atau Tahun tidak valid"}), 400

    start_date = datetime(tahun, bulan, 1).date()
    end_date = datetime(tahun, bulan + 1, 1).date() if bulan < 12 else datetime(tahun + 1, 1, 1).date()

    konfigurasi = KonfigurasiKamerapresensi.query.first()
    if not konfigurasi:
        return jsonify({"error": "Konfigurasi kamera tidak ditemukan"}), 400

    jam_mulai = konfigurasi.jam_mulai_kedatangan
    jam_berakhir = konfigurasi.jam_berakhir_kedatangan

    # Subquery untuk menghitung total ontime
    subquery = (
        db.session.query(
            AbsensiPegawai.pegawai_id,
            func.count(AbsensiPegawai.id).label('total_ontime')
        )
        .filter(AbsensiPegawai.tanggal >= start_date)
        .filter(AbsensiPegawai.tanggal < end_date)
    )

    if filter_ == 'ontime':
        subquery = subquery.filter(
            AbsensiPegawai.presensi_datang >= jam_mulai,
            AbsensiPegawai.presensi_datang <= jam_berakhir
        )
    elif filter_ == 'late':
        subquery = subquery.filter(AbsensiPegawai.presensi_datang > jam_berakhir)
    elif filter_ == 'kerja':
        subquery = subquery.filter(AbsensiPegawai.jam_lembur.isnot(None))

    subquery = subquery.group_by(AbsensiPegawai.pegawai_id).subquery()

    # Join ke tabel pegawai dan divisi
    hasil = (
        db.session.query(
            Pegawai.id.label("id_pegawai"),
            Pegawai.nama_pegawai,
            Divisi.nama_divisi,
            subquery.c.total_ontime
        )
        .join(subquery, subquery.c.pegawai_id == Pegawai.id)
        .outerjoin(Divisi, Divisi.id == Pegawai.divisi_id)
        .order_by(subquery.c.total_ontime.desc())
        .all()
    )

    # Format ke bentuk JSON
    data = [
        {
            "no": i + 1,
            "id_pegawai": row.id_pegawai,
            "nama_pegawai": row.nama_pegawai,
            "divisi": row.nama_divisi or "Tidak ada divisi",
            "total_ontime": row.total_ontime
        }
        for i, row in enumerate(hasil)
    ]

    return jsonify(data)

@app.route('/chart-donat')
def chart_donat():
    user_id = request.cookies.get('pegawai_id')  # Menggunakan pegawai_id dari cookie

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Ambil konfigurasi berdasarkan admin_id yang terhubung dengan pegawai_id
    pegawai = Pegawai.query.get(user_id)
    if not pegawai:
        return jsonify({"error": "Pegawai tidak ditemukan"}), 404

    admin_id = pegawai.admin_id
    konfigurasi = KonfigurasiKamerapresensi.query.filter_by(admin_id=admin_id).first()

    if not konfigurasi:
        return jsonify({"error": "Konfigurasi kamera tidak ditemukan"}), 404

    jam_awal_kedatangan = konfigurasi.jam_mulai_kedatangan
    jam_toleransi_datang = konfigurasi.jam_berakhir_kedatangan
    bulan_ini = datetime.now().strftime('%Y-%m')

    # Ambil data absensi berdasarkan pegawai_id dan bulan yang sesuai
    data = db.session.query(
        AbsensiPegawai.tanggal,
        AbsensiPegawai.presensi_datang,
        AbsensiPegawai.presensi_pulang
    ).filter(
        AbsensiPegawai.pegawai_id == user_id,
        func.date_format(AbsensiPegawai.tanggal, '%Y-%m') == bulan_ini
    ).all()

    total_ontime = 0
    total_late = 0
    total_absen = 0

    for row in data:
        if row.presensi_datang:
            total_absen += 1
            if jam_awal_kedatangan <= row.presensi_datang <= jam_toleransi_datang:
                total_ontime += 1
            elif row.presensi_datang > jam_toleransi_datang:
                total_late += 1


    return jsonify({
        "ontime": total_ontime,
        "late": total_late,
        "total_absen": total_absen
    })


@app.route('/riwayat-hari-ini')
def riwayat_hari_ini():
    raw_id = request.cookies.get('pegawai_id') or request.cookies.get('user_id')
    if not raw_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = int(raw_id)
    except ValueError:
        return jsonify({"error": "Invalid user_id in cookie"}), 400

    today = date.today()
    app.logger.debug(f"[riwayat-hari-ini] user_id: {user_id}, today: {today}")

    # --- QUERY DENGAN ATRIBUT YANG BENAR ---
    data = db.session.query(
        AbsensiPegawai.tanggal,
        Pegawai.nama_pegawai.label("nama_pegawai"),
        Divisi.nama_divisi.label("nama_divisi"),   # ← ganti di sini
        AbsensiPegawai.presensi_datang
    )\
    .join(Pegawai, AbsensiPegawai.pegawai_id == Pegawai.id)\
    .join(Divisi, Pegawai.divisi_id == Divisi.id)\
    .filter(
        AbsensiPegawai.tanggal == today,
        AbsensiPegawai.pegawai_id == user_id
    ).all()

    if not data:
        return jsonify({"message": "Belum ada absensi hari ini"}), 200

    result = []
    for row in data:
        result.append({
            "tanggal": row.tanggal.strftime('%d/%m/%Y'),
            "nama_pegawai": row.nama_pegawai,
            "divisi": row.nama_divisi,
            "presensi_datang": row.presensi_datang.strftime('%H:%M:%S') if row.presensi_datang else "-"
        })

    return jsonify(result), 200

@app.route('/jumlah-perusahaan')
def jumlah_perusahaan():
    jumlah_admin = db.session.query(Admin.id).count()
    jumlah_pegawai = db.session.query(Pegawai.id).count()
    jumlah_perusahaan = jumlah_admin  # karena setiap admin mewakili 1 perusahaan

    return jsonify({
        "jumlah": jumlah_perusahaan,
        "jumlah_admin": jumlah_admin,
        "jumlah_pegawai": jumlah_pegawai
    })

@app.route('/dataset-admin', methods=['GET', 'POST'])
def dataset_admin():
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash('User tidak dikenali.', 'danger')
        return redirect(url_for('login'))

    admin = Admin.query.get(user_id)
    if not admin:
        flash('Admin tidak ditemukan.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        model_file = request.files.get('model_file')
        model_type = request.form.get('model_type')  # <== Ambil jenis model

        # Tentukan field & nama file berdasarkan jenis model
        if model_type == 'pelanggaran':
            db_field = 'model_makanminum'
            filename_suffix = '_makanminum_model.pt'
        else:
            db_field = 'model_path'
            filename_suffix = '_model.pt'

        filename = f"{admin.nama_instansi}{filename_suffix}"
        model_folder = os.path.join(app.root_path, 'static', 'models')
        file_path = os.path.join(model_folder, filename)

        if action == 'upload':
            if model_file and model_file.filename.endswith('.pt'):
                try:
                    os.makedirs(model_folder, exist_ok=True)
                    model_file.save(file_path)

                    setattr(admin, db_field, f"models/{filename}")
                    db.session.commit()

                    flash(f'Model {model_type} berhasil diupload.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Gagal upload model: {str(e)}', 'danger')
            else:
                flash('File tidak valid. Harus .pt', 'warning')

        elif action == 'edit':
            if model_file and model_file.filename.endswith('.pt'):
                try:
                    os.makedirs(model_folder, exist_ok=True)

                    # Hapus file lama jika ada
                    old_path = getattr(admin, db_field)
                    if old_path:
                        old_full_path = os.path.join(app.root_path, 'static', old_path)
                        if os.path.exists(old_full_path):
                            os.remove(old_full_path)

                    model_file.save(file_path)
                    setattr(admin, db_field, f"models/{filename}")
                    db.session.commit()

                    flash(f'Model {model_type} berhasil diperbarui.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Gagal edit model: {str(e)}', 'danger')
            else:
                flash('File tidak valid. Harus .pt', 'warning')

        elif action == 'delete':
            try:
                old_path = getattr(admin, db_field)
                if old_path:
                    old_full_path = os.path.join(app.root_path, 'static', old_path)
                    if os.path.exists(old_full_path):
                        os.remove(old_full_path)

                    setattr(admin, db_field, None)
                    db.session.commit()
                    flash(f'Model {model_type} berhasil dihapus.', 'success')
                else:
                    flash('Tidak ada model yang dihapus.', 'info')
            except Exception as e:
                db.session.rollback()
                flash(f'Gagal hapus model: {str(e)}', 'danger')

        return redirect(url_for('dataset_admin'))

    return render_template('dataset_admin.html', admin=admin, username=session.get('username'),
    role=session.get('role'))

@app.route('/pegawai_upload', methods=['GET', 'POST'])
def upload_photo():
    if request.method == 'POST':
        name = request.form.get('name')
        photos = request.files.getlist('photos')

        pegawai_id = request.cookies.get('pegawai_id')
        admin_id = request.cookies.get('admin_id')
        username = request.cookies.get('username')

        if not pegawai_id or not admin_id or not username:
            return jsonify({'success': False, 'message': 'Informasi login tidak lengkap di cookies'})

        pegawai = Pegawai.query.filter_by(id=pegawai_id, admin_id=admin_id, username=username).first()

        if not pegawai:
            return jsonify({'success': False, 'message': 'Data pegawai tidak ditemukan atau tidak valid'})

        if name != pegawai.nama_pegawai:
            return jsonify({'success': False, 'message': 'Nama pegawai tidak cocok dengan akun login'})

        if not photos:
            return jsonify({'success': False, 'message': 'Foto tidak ditemukan'})

        base_dir = os.path.join(app.root_path, 'static', 'foto_dataset')
        folder_path = os.path.join(base_dir, f'admin_{admin_id}', secure_filename(pegawai.nama_pegawai))
        os.makedirs(folder_path, exist_ok=True)

        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = os.path.basename(photo.filename)
                photo.save(os.path.join(folder_path, secure_filename(filename)))

        rel_path = os.path.relpath(folder_path, app.root_path)
        pegawai.folder_path = rel_path
        db.session.commit()

        return jsonify({'success': True})

    # Ambil dari session untuk GET request
    if 'username' not in session or 'role' not in session:
        return redirect(url_for('login'))

    username = session['username']
    role = session['role']

    return render_template('pegawai_upload.html', username=username, role=role)




@app.route("/get_foto_in_folder")
def get_foto_in_folder():
    folder_name = request.args.get("name")
    admin_id = request.cookies.get("admin_id")  # GANTI dari session.get

    print("Admin ID:", admin_id)
    print("Folder name:", folder_name)

    if not admin_id or not folder_name:
        return jsonify({"fotos": []})

    folder_path = os.path.join("static", "foto_dataset", f"admin_{admin_id}", folder_name)
    print("Folder path:", folder_path)

    if not os.path.isdir(folder_path):
        return jsonify({"fotos": []})

    foto_files = [
        os.path.join("/", folder_path, f).replace("\\", "/")
        for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
    ]

    return jsonify({"fotos": foto_files})


@app.route('/list_folders', methods=['GET'])
def list_folders():
    # Ambil ID admin dari cookie (misalnya dari 'admin_id')
    admin_id = request.cookies.get('admin_id')

    # Pastikan admin_id valid
    if not admin_id:
        return jsonify({"folders": []})

    # Lokasi folder dataset untuk admin ini
    base_path = os.path.join('static', 'foto_dataset', f'admin_{admin_id}')
    
    if not os.path.exists(base_path):
        return jsonify({"folders": []})

    # Ambil nama folder di dalamnya (nama pegawai)
    folders = [name for name in os.listdir(base_path)
               if os.path.isdir(os.path.join(base_path, name))]

    return jsonify({"folders": folders})

@app.route('/delete_folder')
def delete_folder():
    folder = request.args.get('name')
    admin_id = request.cookies.get("admin_id")
    folder_path = os.path.join('static', 'foto_dataset', f'admin_{admin_id}', folder)
    
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    return '', 204

@app.route('/delete_all_folders')
def delete_all_folders():
    admin_id = request.cookies.get("admin_id")
    base_path = os.path.join('static', 'foto_dataset', f'admin_{admin_id}')
    if os.path.exists(base_path):
        for folder in os.listdir(base_path):
            full_path = os.path.join(base_path, folder)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
    return '', 204

@app.route('/download_folder')
def download_folder():
    folder_name = request.args.get('name')
    admin_id = request.cookies.get("admin_id")
    folder_path = os.path.join('static', 'foto_dataset', f'admin_{admin_id}', folder_name)

    # ZIP-in dalam memori
    zip_stream = io.BytesIO()
    with zipfile.ZipFile(zip_stream, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.join(folder_path, '..'))
                zf.write(file_path, arcname)
    zip_stream.seek(0)

    return send_file(zip_stream, mimetype='application/zip', as_attachment=True, download_name=f"{folder_name}.zip")



# Fungsi untuk menghasilkan nama file unik
def generate_unique_filename(extension):
    return f"{uuid.uuid4()}.{extension}"

# Warna yang akan digunakan untuk bounding box setiap kelas
colors = {
0: (0, 0, 255), 
1: (0, 255, 0),
2: (255, 0, 0),
3: (255, 255, 0),


}

def load_class_names(admin_id, model_path):
    # Cek apakah file .txt tersedia
    class_txt_path = os.path.join(os.path.dirname(model_path), "class_names.txt")
    if os.path.exists(class_txt_path):
        with open(class_txt_path, 'r') as f:
            names = f.read().splitlines()
        class_names = {i: name for i, name in enumerate(names)}
    else:
        # Fallback: extract dari model .pt langsung
        model = YOLO(model_path)
        class_names = model.names

    class_names_by_admin[admin_id] = class_names


# Fungsi untuk menambahkan kotak deteksi dan label ke gambar
def custom_plot(results, detected_persons, class_names, frame=None, thickness=2, font_scale=1.0, color_override=None):
    img = frame if frame is not None else results[0].orig_img  # Gunakan frame jika diberikan

    for box in results[0].boxes:
        cls = int(box.cls[0])
        confidence = box.conf[0]

        if confidence < 0.5:
            continue

        label_name = class_names.get(cls, f"ID-{cls}")
        label = f"{label_name} {confidence:.2f}"

        # Tentukan warna berdasarkan label_name
        if color_override:
            color = color_override
        else:
            if label_name.lower() == "makanan":
                color = (255, 0, 0)  # Biru
            elif label_name.lower() == "minuman":
                color = (0, 0, 255)  # Merah
            else:
                color = (0, 255, 0)  # Hijau untuk orang/presensi

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            img,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness
        )

        detection_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cv2.putText(
            img,
            detection_time,
            (x1, y2 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale * 0.8,
            color,
            thickness
        )

        detected_persons.add(label_name)

    return img

# Membuat tabel secara otomatis dan menambah data superadmin pertama kali
with app.app_context():
    db.create_all()

    # Cek apakah superadmin sudah ada di database, jika belum tambahkan
    superadmin_exists = Superadmin.query.filter_by(username='superadmin').first()
    if not superadmin_exists:
        # Menambahkan superadmin pertama kali
       # Menambahkan superadmin pertama kali
        new_superadmin = Superadmin(username='superadmin', password='superadmin123', role='superadmin')
        db.session.add(new_superadmin)
        db.session.commit()


def get_kamera_configs(admin_id=None, use_webcam=False):
    with app.app_context():
        kamera_configs = []
        
        if not use_webcam:  # Jika tidak menggunakan webcam, ambil dari database
            if admin_id:
                kamera_configs = KonfigurasiKamerapresensi.query.filter_by(admin_id=admin_id).all()
            else:
                kamera_configs = KonfigurasiKamerapresensi.query.all()
        else:  # Jika menggunakan webcam, tambahkan sebagai opsi
            kamera_configs.append({
                "ip_rtsp": 0,  # Webcam default (bisa diganti dengan 1 untuk kamera eksternal)
                "role_kamera": "in"
            })

        return kamera_configs



# Ambil semua RTSP URL dari database
def get_rtsp_urls(admin_id=None):
    with app.app_context():
        if admin_id:
            presensi_list = KonfigurasiKamerapresensi.query.filter_by(admin_id=admin_id).all()
        else:
            presensi_list = KonfigurasiKamerapresensi.query.all()

        pelacakan_list = KonfigurasiKamerapelacakankerja.query.all()

        rtsp_presensi = [kamera.ip_rtsp for kamera in presensi_list] if presensi_list else []
        rtsp_pelacakan = [kamera.ip_rtsp for kamera in pelacakan_list] if pelacakan_list else []

        return rtsp_presensi, rtsp_pelacakan



# Ambil semua RTSP URL dari database
rtsp_presensi, rtsp_pelacakan = get_rtsp_urls()

if not rtsp_presensi and not rtsp_pelacakan:
    raise ValueError("RTSP URL tidak ditemukan di database!")

kamera_configs = get_kamera_configs()
valid_rtsp_presensi_in = []
valid_rtsp_presensi_out = []
caps_presensi_in = []
caps_presensi_out = []
caps_pelacakan = []
valid_rtsp_pelacakan = []

# Inisialisasi kamera presensi
for kamera in kamera_configs:
    cap = cv2.VideoCapture(kamera.ip_rtsp)
    if cap.isOpened():
        if kamera.role_kamera.value == 'in':
            valid_rtsp_presensi_in.append(kamera.ip_rtsp)
            caps_presensi_in.append(cap)
        elif kamera.role_kamera.value == 'out':
            valid_rtsp_presensi_out.append(kamera.ip_rtsp)
            caps_presensi_out.append(cap)
    else:
        print(f"❌ Kamera {kamera.role_kamera.value} dengan URL {kamera.ip_rtsp} tidak aktif, dilewati.")

# Inisialisasi kamera pelacakan kerja
for url in rtsp_pelacakan:
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        caps_pelacakan.append(cap)
        valid_rtsp_pelacakan.append(url)
    else:
        print(f"❌ Kamera pelacakan kerja dengan URL {url} tidak aktif, dilewati.")

# Lock dan buffer untuk masing-masing kamera
frame_locks_in = [threading.Lock() for _ in valid_rtsp_presensi_in]
latest_frames_in = [None] * len(valid_rtsp_presensi_in)

frame_locks_out = [threading.Lock() for _ in valid_rtsp_presensi_out]
latest_frames_out = [None] * len(valid_rtsp_presensi_out)

frame_locks_pelacakan = [threading.Lock() for _ in valid_rtsp_pelacakan]
latest_frames_pelacakan = [None] * len(valid_rtsp_pelacakan)


attendance_log_today = {}
last_logged_time = {}
reset_time = datetime.combine(datetime.now().date(), datetime.min.time()) + timedelta(days=1)

def reset_attendance_log():
    global attendance_log_today, last_logged_time, reset_time
    attendance_log_today = {}
    last_logged_time = {}
    reset_time = datetime.combine(datetime.now().date(), datetime.min.time()) + timedelta(days=1)

def frame_grabber(index, caps, latest_frames, frame_locks):
    """Thread untuk mengambil frame dari setiap kamera."""
    while True:
        success, frame = caps[index].read()
        if not success:
            print(f"❌ Gagal membaca frame dari kamera {index + 1}")
            continue
        with frame_locks[index]:
            latest_frames[index] = frame


# Mulai thread untuk mengambil frame dari kamera presensi
threads_in = [
    threading.Thread(target=frame_grabber, args=(i, caps_presensi_in, latest_frames_in, frame_locks_in), daemon=True)
    for i in range(len(valid_rtsp_presensi_in))
]
for thread in threads_in:
    thread.start()

threads_out = [
    threading.Thread(target=frame_grabber, args=(i, caps_presensi_out, latest_frames_out, frame_locks_out), daemon=True)
    for i in range(len(valid_rtsp_presensi_out))
]
for thread in threads_out:
    thread.start()

# Mulai thread untuk mengambil frame dari kamera pelacakan kerja
threads_pelacakan = [
    threading.Thread(target=frame_grabber, args=(i, caps_pelacakan, latest_frames_pelacakan, frame_locks_pelacakan), daemon=True)
    for i in range(len(valid_rtsp_pelacakan))
]
for thread in threads_pelacakan:
    thread.start()

# Fungsi untuk menangani streaming video dengan deteksi YOLO
def generate_frames(index, latest_frames, frame_locks, admin_id, role_kamera):
    """Menghasilkan frame yang diolah untuk streaming dari kamera tertentu."""
    global attendance_log_today, last_logged_time
    detection_start_times = {}  # Menyimpan waktu mulai deteksi untuk setiap orang

    model = None  # Pastikan variabel model dideklarasikan di awal
    class_names = {}

    while True:
        with frame_locks[index]:
            if latest_frames[index] is None:
                continue
            frame = latest_frames[index].copy()

        resized_frame = cv2.resize(frame, (640, 360))

        if admin_id is None:
            print(" admin_id kosong!")
            time.sleep(1)
            continue

        if model is None:
            model = models_by_admin.get(admin_id)
            if model is None:
                    print(f" Model belum dimuat, mencoba muat ulang...")
                    try:
                        with app.app_context():
                            admin_data = Admin.query.get(admin_id)
                            if not admin_data or not admin_data.model_path:
                                print(f" Admin dengan ID {admin_id} tidak ditemukan atau model_path kosong.")
                                time.sleep(1)
                                continue

                            model_path = os.path.join(app.root_path, 'static', admin_data.model_path)
                            if not os.path.exists(model_path):
                                print(f" Model path tidak ditemukan: {model_path}")
                                time.sleep(1)
                                continue

                            model = YOLO(model_path)
                            models_by_admin[int(admin_id)] = model
                            print(f" Model untuk admin_id {admin_id} berhasil dimuat dari {model_path}")
                    #  Load class names dari .txt atau model
                            txt_path = model_path.replace('.pt', '.txt')
                            if os.path.exists(txt_path):
                                with open(txt_path, 'r') as f:
                                    names = [line.strip() for line in f.readlines()]
                                class_names = {i: name for i, name in enumerate(names)}
                                print(f" class_names berhasil dimuat dari .txt untuk admin_id {admin_id}")
                            else:
                                class_names = model.names
                                print(f" File .txt tidak ditemukan. Menggunakan class_names dari model.pt")

                            class_names_by_admin[int(admin_id)] = class_names

                    except Exception as e:
                        print(f" Gagal memuat model untuk admin_id {admin_id}: {e}")
                        time.sleep(1)
                        continue

            #  Pastikan class_names tersedia di semua jalur
            class_names = class_names_by_admin.get(int(admin_id), {})

        results = model(resized_frame)
        detected_persons = set()
        frame_with_boxes = custom_plot(results, detected_persons, class_names)

        # Jika ada objek yang terdeteksi
        if len(results[0].boxes) > 0:
            detected_classes = {int(box.cls[0]) for box in results[0].boxes if box.conf[0] >= 0.5}
            current_time = time.time()
            current_date = datetime.now().strftime("%d-%m-%Y")
            current_datetime = datetime.now()
            
            person_name = "Unknown"
            for cls_index in detected_classes:
                person_name = class_names.get(cls_index, "Unknown")
                
            with app.app_context():
                pegawai = Pegawai.query.filter_by(nama_pegawai=person_name).first()
                config = KonfigurasiKamerapresensi.query.filter_by(role_kamera=role_kamera).first()

                if pegawai and config:
                    if role_kamera == "in":
                        if person_name not in attendance_log_today:
                            if person_name not in detection_start_times:
                                detection_start_times[person_name] = current_time
                            elif current_time - detection_start_times[person_name] >= 5:
                                image_filename = generate_unique_filename("jpg")
                                image_path = os.path.join('static', 'images', image_filename)
                                cv2.imwrite(image_path, frame_with_boxes)

                                detected_persons.add(person_name)

                                new_absensi = AbsensiPegawai(
                                    pegawai_id=pegawai.id,
                                    tanggal=current_datetime.date(),
                                    presensi_datang=current_datetime.time(),
                                    foto_datang=f'images/{image_filename}',
                                    jam_kerja=config.jam_berakhir_kedatangan,
                                    jam_selesai_kerja=config.jam_berakhir_pulang,
                                    admin_id=admin_id,
                                    status="Belumpulang"
                                )
                                db.session.add(new_absensi)
                                db.session.commit()

                                #  Kirim WhatsApp setelah absensi dicatat
                                send_whatsapp_message(
                                    person_name,
                                    "Presensi Datang",
                                    current_datetime.strftime("%d-%m-%Y %H:%M:%S"),
                                    role_kamera,
                                    f'images/{image_filename}'
                                )

                                attendance_log_today[person_name] = current_date
                                last_logged_time[person_name] = current_time
                                del detection_start_times[person_name]

                    elif role_kamera == "out":
                        absensi = AbsensiPegawai.query.filter_by(pegawai_id=pegawai.id, tanggal=current_datetime.date()).first()
                        if absensi and absensi.presensi_pulang is None:
                            image_filename = generate_unique_filename("jpg")
                            image_path = os.path.join('static', 'images', image_filename)
                            cv2.imwrite(image_path, frame_with_boxes)

                            presensi_pulang_time = current_datetime.time()
                            jam_selesai_kerja = datetime.strptime(str(absensi.jam_selesai_kerja), "%H:%M:%S").time()
                            selisih_detik = (datetime.combine(date.today(), presensi_pulang_time) -
                            datetime.combine(date.today(), jam_selesai_kerja)).total_seconds()
                            if selisih_detik > 0:
                                jam = int(selisih_detik // 3600)
                                menit = int((selisih_detik % 3600) // 60)
                                absensi.jam_lembur = dt_time(hour=jam, minute=menit, second=0)
                            else:
                                absensi.jam_lembur = dt_time(0, 0, 0)


                            absensi.presensi_pulang = presensi_pulang_time
                            absensi.foto_pulang = f'images/{image_filename}'
                            db.session.commit()

                            #  Kirim WhatsApp setelah absensi keluar dicatat
                            send_whatsapp_message(
                                person_name,
                                "Presensi Pulang",
                                current_datetime.strftime("%d-%m-%Y %H:%M:%S"),
                                role_kamera,
                                f'images/{image_filename}'
                            )


        ret, buffer = cv2.imencode('.jpg', frame_with_boxes)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
time.sleep(0.05)

def check_available_cameras():
    """ Mengecek jumlah kamera yang tersedia """
    available_cameras = []
    for index in range(5):  # Coba hingga 5 index, tergantung jumlah port USB yang tersedia
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.read()[0]:
            available_cameras.append(index)
        cap.release()
    return available_cameras

AVAILABLE_CAMERAS = check_available_cameras()


@app.route("/check_webcams")
def check_webcams():
    return {"count": len(AVAILABLE_CAMERAS)}

# Fungsi untuk menangani streaming video dengan deteksi YOLO Lama Kerja
def generate_frames_lama_kerja(index, latest_frames, frame_locks, admin_id_cookie):
    global attendance_log_today, last_logged_time

    detection_start_times = {}
    detection_in_progress = {}
    bukti_foto = {}

    try:
        admin_id = int(admin_id_cookie)
    except (TypeError, ValueError):
        print("❌ admin_id_cookie tidak valid!")
        return

    with app.app_context():
        configs = KonfigurasiKamerapelacakankerja.query.filter_by(admin_id=admin_id).all()
        admin_data = Admin.query.get(admin_id)
        print("🧪 admin_data.model_makanminum:", admin_data.model_makanminum)

        pegawai_dict = {
            p.nama_pegawai: {"id": p.id, "divisi": p.divisi}
            for p in Pegawai.query.all()
        }

    if index >= len(configs):
        print(f"[WARNING] Index {index} melebihi jumlah konfigurasi kamera untuk admin_id={admin_id}")
        return

    config = configs[index]

    # === MODEL PRESENSI ===
    model = models_by_admin.get(admin_id)
    class_names = class_names_by_admin.get(admin_id, {})

    if model is None:
        try:
            model_path = os.path.join(app.root_path, 'static', admin_data.model_path)
            if not os.path.exists(model_path):
                print(f"❌ Model path tidak ditemukan: {model_path}")
                return

            model = YOLO(model_path)
            models_by_admin[admin_id] = model

            txt_path = model_path.replace('.pt', '.txt')
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as f:
                    names = [line.strip() for line in f.readlines()]
                class_names = {i: name for i, name in enumerate(names)}
            else:
                class_names = model.names

            class_names_by_admin[admin_id] = class_names
        except Exception as e:
            print(f"❌ Gagal memuat model presensi: {e}")
            return

    # === MODEL PELANGGARAN ===
    model_pelanggaran = model_pelanggaran_by_admin.get(admin_id)
    if model_pelanggaran is None:
        try:
            model_path_pelanggaran = os.path.join(app.root_path, 'static', admin_data.model_makanminum)
            print(f"📦 Mencoba load model pelanggaran dari: {model_path_pelanggaran}")
            if not os.path.exists(model_path_pelanggaran):
                print(f"❌ Model pelanggaran tidak ditemukan: {model_path_pelanggaran}")
                return

            model_pelanggaran = YOLO(model_path_pelanggaran)
            model_pelanggaran_by_admin[admin_id] = model_pelanggaran
            print(f"✅ Model pelanggaran dimuat untuk admin_id={admin_id}")
        except Exception as e:
            print(f"❌ Gagal memuat model pelanggaran: {e}")
            return

    while True:
        time.sleep(0.01)

        with frame_locks[index]:
            if latest_frames[index] is None:
                continue
            frame = latest_frames[index].copy()

        resized_frame = cv2.resize(frame, (640, 360))
        results = model(resized_frame, verbose=False)
        results_pelanggaran = model_pelanggaran(resized_frame, verbose=False)

        # Update waktu saat ini
        current_time = time.time()
        current_datetime = datetime.now()

        # Plot presensi dan pelanggaran
        frame_with_boxes = custom_plot(results, set(), class_names)
        frame_with_boxes = custom_plot(results_pelanggaran, set(), model_pelanggaran.names, frame=frame_with_boxes)

        detected_names = set()

        # === DETEKSI ORANG UNTUK PRESENSI ===
        if results and results[0].boxes:
            for box in results[0].boxes:
                if box.conf[0] < 0.4:
                    continue
                cls_index = int(box.cls[0])
                person_name = class_names.get(cls_index, "Unknown")
                if person_name == "Unknown":
                    continue
                detected_names.add(person_name)

                if not detection_in_progress.get(person_name):
                    detection_start_times[person_name] = current_time
                    detection_in_progress[person_name] = True
                    bukti_foto[person_name] = frame_with_boxes.copy()

        # === SIMPAN PRESENSI JIKA ORANG SUDAH TIDAK TERDETEKSI ===
        for person_name in list(detection_in_progress):
            if person_name not in detected_names:
                durasi = int(current_time - detection_start_times[person_name])
                pegawai_data = pegawai_dict.get(person_name)
                if not pegawai_data:
                    continue

                img_bukti = None
                if person_name in bukti_foto:
                    os.makedirs(os.path.join('static', 'bukti'), exist_ok=True)
                    filename_bukti = f"{person_name}_{int(time.time())}_bukti.jpg"
                    path_bukti = os.path.join('static', 'bukti', filename_bukti)
                    cv2.imwrite(path_bukti, bukti_foto[person_name])
                    img_bukti = path_bukti

                pelanggaran_terdeteksi = False
                foto_pelanggaran = None

                # === CEK PELANGGARAN ===
                if results_pelanggaran and results_pelanggaran[0].boxes:
                    for box in results_pelanggaran[0].boxes:
                        conf = box.conf[0]
                        cls_idx = int(box.cls[0])
                        class_name = model_pelanggaran.names[cls_idx]
                        print(f"[🔍 DEBUG PELANGGARAN] Deteksi kelas: {class_name}, Confidence: {conf:.2f}")
                        if conf < 0.5:
                            continue
                        if class_name.lower() in ['makan', 'minum', 'makanan', 'minuman', 'botol', 'cup']:
                            pelanggaran_terdeteksi = True
                            os.makedirs(os.path.join('static', 'pelanggaran'), exist_ok=True)
                            filename_pelanggaran = f"{person_name}_{int(time.time())}_pelanggaran.jpg"
                            path_pelanggaran = os.path.join('static', 'pelanggaran', filename_pelanggaran)
                            cv2.imwrite(path_pelanggaran, frame.copy())
                            foto_pelanggaran = path_pelanggaran

                            # ✅ Tambahkan baris ini:
                            threading.Thread(target=play_sound, daemon=True).start()

                            print(f"🚨 Pelanggaran terdeteksi: {class_name.upper()} oleh {person_name}")
                            break

                # === SIMPAN KE DATABASE ===
                try:
                    with app.app_context():
                        record = LamaKerja.query.filter_by(
                            pegawai_id=pegawai_data['id'],
                            admin_id=admin_id,
                            tanggal=current_datetime.date(),
                            area_cctv=config.nama_kamera
                        ).first()

                        if record:
                            record.lama_terdeteksi += durasi
                            if pelanggaran_terdeteksi:
                                record.pelanggaran = "Makan/Minum"
                                record.foto_pelanggaran = foto_pelanggaran
                        else:
                            record = LamaKerja(
                                pegawai_id=pegawai_data['id'],
                                admin_id=admin_id,
                                tanggal=current_datetime.date(),
                                nama_pegawai=person_name,
                                divisi=pegawai_data['divisi'],
                                lama_terdeteksi=durasi,
                                area_cctv=config.nama_kamera,
                                foto_bukti=img_bukti,
                                pelanggaran="Makan/Minum" if pelanggaran_terdeteksi else None,
                                foto_pelanggaran=foto_pelanggaran if pelanggaran_terdeteksi else None
                            )
                            db.session.add(record)

                        db.session.commit()
                        print(f"✅ Data lama kerja disimpan untuk {person_name}, durasi {durasi}s")
                        if pelanggaran_terdeteksi:
                            print(f"📸 Foto pelanggaran juga disimpan.")
                except Exception as e:
                    print(f"[ERROR] DB error: {e}")
                    db.session.rollback()

                # Bersihkan state
                detection_in_progress.pop(person_name, None)
                detection_start_times.pop(person_name, None)
                bukti_foto.pop(person_name, None)

        # Encode dan kirim ke client
        ret, buffer = cv2.imencode('.jpg', frame_with_boxes)
        if not ret:
            continue

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def play_sound():
    pygame.mixer.init()
    pygame.mixer.music.load('static/sounds/alarm.mp3')
    pygame.mixer.music.play()

# Tambahkan di global scope aplikasi Flask
rtsp_sources = {}
thread_stop_flags = {}
running_threads = {}
latest_frames_pelacakan = []
frame_locks_pelacakan = []

latest_frames_dict = {'in': [], 'out': []}
frame_locks_dict = {'in': [], 'out': []}
rtsp_sources_dict = {'in': {}, 'out': {}}
thread_stop_flags_dict = {'in': {}, 'out': {}}
running_threads_dict = {'in': {}, 'out': {}}


@app.route('/video_feed/presensi/<string:role_kamera>/<int:index>/<string:use_webcam>')
def video_feed_presensi(role_kamera, index, use_webcam):
    from flask import request, Response
    import threading
    import cv2

    admin_id = request.cookies.get('user_id')
    use_webcam = use_webcam.lower() == 'true'
    role = role_kamera.lower()

    # Pastikan role valid
    if role not in ['in', 'out']:
        return "Role kamera tidak valid!", 400

    # Inisialisasi dict jika perlu
    for d in [latest_frames_dict, frame_locks_dict, rtsp_sources_dict, thread_stop_flags_dict, running_threads_dict]:
        if role not in d:
            d[role] = [] if 'frames' in str(d) else {}

    if use_webcam:
        if index >= len(AVAILABLE_CAMERAS):
            return f"Kamera webcam dengan index {index} tidak ditemukan!", 404

        cap = cv2.VideoCapture(AVAILABLE_CAMERAS[index], cv2.CAP_DSHOW)

        while len(latest_frames_dict[role]) <= index:
            latest_frames_dict[role].append(None)
            frame_locks_dict[role].append(threading.Lock())

        def capture_webcam_frames():
            while True:
                with frame_locks_dict[role][index]:
                    ret, frame = cap.read()
                    if ret:
                        latest_frames_dict[role][index] = frame

        threading.Thread(target=capture_webcam_frames, daemon=True).start()

        return Response(
            generate_frames(index, latest_frames_dict[role], frame_locks_dict[role], admin_id, role),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    else:
        kamera_list = KonfigurasiKamerapresensi.query.filter_by(role_kamera=role).all()
        if index >= len(kamera_list):
            return f"Kamera RTSP dengan role {role.upper()} index {index} tidak ditemukan!", 404

        kamera = kamera_list[index]
        rtsp_url = kamera.ip_rtsp

        while len(latest_frames_dict[role]) <= index:
            latest_frames_dict[role].append(None)
            frame_locks_dict[role].append(threading.Lock())

        rtsp_changed = (
            index not in rtsp_sources_dict[role] or rtsp_sources_dict[role][index] != rtsp_url
        )

        if rtsp_changed:
            if index in thread_stop_flags_dict[role]:
                thread_stop_flags_dict[role][index].set()

            stop_event = threading.Event()
            thread_stop_flags_dict[role][index] = stop_event
            rtsp_sources_dict[role][index] = rtsp_url

            def capture_rtsp_frames(rtsp, idx, stop_event):
                cap = cv2.VideoCapture(rtsp)
                while not stop_event.is_set():
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    with frame_locks_dict[role][idx]:
                        latest_frames_dict[role][idx] = frame
                cap.release()

            t = threading.Thread(
                target=capture_rtsp_frames,
                args=(rtsp_url, index, stop_event),
                daemon=True
            )
            running_threads_dict[role][index] = t
            t.start()

        return Response(
            generate_frames(index, latest_frames_dict[role], frame_locks_dict[role], admin_id, role),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

@app.route('/video_feed/lama_kerja/<int:admin_kamera_pelacakan_realtime>')
def video_feed_lama_kerja(admin_kamera_pelacakan_realtime):
    admin_id = request.cookies.get('user_id')


    # Ambil konfigurasi kamera dari database
    konfigurasi_kamera = KonfigurasiKamerapelacakankerja.query.filter_by(admin_id=admin_id).all()
    valid_rtsp_pelacakan = [kamera.ip_rtsp for kamera in konfigurasi_kamera if kamera.ip_rtsp]


    if admin_kamera_pelacakan_realtime >= len(valid_rtsp_pelacakan):
        return f"Kamera dengan index {admin_kamera_pelacakan_realtime} tidak ditemukan!", 404


    current_rtsp = valid_rtsp_pelacakan[admin_kamera_pelacakan_realtime]


    # Perpanjang list jika perlu
    while len(latest_frames_pelacakan) <= admin_kamera_pelacakan_realtime:
        latest_frames_pelacakan.append(None)
    while len(frame_locks_pelacakan) <= admin_kamera_pelacakan_realtime:
        frame_locks_pelacakan.append(threading.Lock())


    # Cek perubahan RTSP
    rtsp_changed = (
        admin_kamera_pelacakan_realtime not in rtsp_sources or
        rtsp_sources[admin_kamera_pelacakan_realtime] != current_rtsp
    )


    if rtsp_changed:
        print(f"[INFO] RTSP kamera {admin_kamera_pelacakan_realtime} berubah, restart stream...")


        # Set stop flag untuk thread lama (jika ada)
        if admin_kamera_pelacakan_realtime in thread_stop_flags:
            thread_stop_flags[admin_kamera_pelacakan_realtime].set()


        stop_event = threading.Event()
        thread_stop_flags[admin_kamera_pelacakan_realtime] = stop_event
        rtsp_sources[admin_kamera_pelacakan_realtime] = current_rtsp


        # Buat thread baru
        def frame_grabber_thread(index, rtsp, stop_event):
            print(f"[THREAD START] Kamera {index} aktif")
            cap = cv2.VideoCapture(rtsp)
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    continue
                with frame_locks_pelacakan[index]:
                    latest_frames_pelacakan[index] = frame
            cap.release()
            print(f"[THREAD STOP] Kamera {index} berhenti")


        t = threading.Thread(
            target=frame_grabber_thread,
            args=(admin_kamera_pelacakan_realtime, current_rtsp, stop_event),
            daemon=True
        )
        running_threads[admin_kamera_pelacakan_realtime] = t
        t.start()


    return Response(
        generate_frames_lama_kerja(
            admin_kamera_pelacakan_realtime,
            latest_frames_pelacakan,
            frame_locks_pelacakan,
            admin_id
        ),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )



if __name__ == '__main__':
    app.run(debug=True)



