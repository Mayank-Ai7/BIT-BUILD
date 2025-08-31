# 📌 Attendance App

A **QR Code-based Attendance Management System** built with **Python** and **Kivy**. This application allows teachers and students to manage attendance digitally by scanning QR codes, making the process seamless and efficient.

---

## 🚀 Features

* **Login System** for Students and Teachers.
* **Teacher Dashboard** to:

  * Generate QR codes for classes/subjects.
  * View and manage attendance records.
* **Student Dashboard** to:

  * Scan QR codes for attendance using webcam.
  * View personal attendance reports.
* **QR Code Integration** (via `qrcode`, `pyzbar`, `opencv`).
* **CSV-based storage** for attendance (`attendance.csv`).
* **GUI built with Kivy** for a smooth cross-platform experience.

---

## 📂 Project Structure

```
attendance_app/
├── main.py                 # Entry point
├── app.py                  # Core AttendanceApp logic
├── attendance.csv          # Stores attendance records
├── qr_codes/               # Auto-generated QR codes
├── screens/                # All GUI screen definitions
│   ├── login.py
│   ├── student_login.py
│   ├── student_dashboard.py
│   ├── student_attendance.py
│   ├── teacher_login.py
│   ├── teacher_dashboard.py
│   └── attendance_view.py
├── utils/
│   └── helpers.py          # Utility functions
├── assets (images/icons)   # PNG background & UI assets
```

---

## 🛠️ Installation & Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd attendance_app
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies

```bash
pip install -r req.txt
```

> If `requirements.txt` is missing, manually install:

```bash
pip install kivy opencv-python pyzbar pillow qrcode pandas
```

### 4. Run the app

```bash
python attendance_app/main.py
```

---

## 🔮 Future Improvements

* Migrate from CSV to **SQLite/Database** backend.
* Add **authentication with hashed passwords**.
* Export attendance reports in **Excel/PDF**.
* Add **face recognition** alongside QR codes for enhanced security.

---

## 👨‍💻 Author

Developed by Team Wecancode✨

---

## 📜 License

This project is licensed under the MIT License. Feel free to use and modify.
