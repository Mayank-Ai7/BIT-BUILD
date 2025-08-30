import os
import subprocess
import pandas as pd

# ---------- Data / constants (unchanged) ----------
TEACHER_CREDENTIALS = {
    "DMS": ("DMS_teacher", "passDMS"),
    "COA": ("COA_teacher", "passCOA"),
    "TOC": ("TOC_teacher", "passTOC"),
    "DBMS": ("DBMS_teacher", "passDBMS"),
    "OOPSJ": ("OOPSJ_teacher", "passOOPSJ"),
    "LMP-2": ("LMP2_teacher", "passLMP2"),
    "LOOPSJ": ("LOOPSJ_teacher", "passLOOPSJ"),
    "LCOA": ("LCOA_teacher", "passLCOA"),
    "LDBMS": ("LDBMS_teacher", "passLDBMS")
}
EXPECTED_WIFI = "Mayank"
CSV_FILE = "attendance.csv"

students = {
    "11": ("Arin", "arin"),
    "28": ("Mayank", "mayank"),
    "19": ("Gatik", "gatik"),
}

SUBJECTS = ["DMS", "COA", "TOC", "DBMS", "OOPSJ", "LMP-2", "LOOPSJ", "LCOA", "LDBMS"]


def get_wifi_ssid():
    """Call netsh and parse output (unchanged logic)."""
    try:
        result = subprocess.check_output(
            "netsh wlan show interfaces", shell=True
        ).decode("utf-8", errors="ignore")
        for line in result.split("\n"):
            if "SSID" in line and ":" in line:
                return line.split(":", 1)[1].strip()
    except Exception as e:
        print("Error getting WiFi SSID:", e)
    return None


def update_attendance(student_name, subject):
    """Load CSV, increment the subject column for the named student (unchanged behavior)."""
    try:
        df = pd.read_csv(CSV_FILE)
        if subject in df.columns and student_name in df["Name"].values:
            df.loc[df["Name"] == student_name, subject] = (
                df.loc[df["Name"] == student_name, subject].astype(int) + 1
            )
            df.to_csv(CSV_FILE, index=False)
            print(f"Attendance updated for {student_name} in {subject}.")
            return True
        print("Invalid Subject or Student Name")
        return False
    except Exception as e:
        print("Error updating attendance:", e)
        return False


def ensure_attendance_csv():
    """Create CSV with zeroed subjects if missing (unchanged behavior)."""
    if not os.path.exists(CSV_FILE):
        data = []
        for sid, (name, _) in students.items():
            row = {"Name": name}
            for subj in SUBJECTS:
                row[subj] = 0
            data.append(row)
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
        print("Created new attendance.csv")
