import subprocess
import psycopg2
from datetime import datetime
import re


# Database connection parameters
DB_CONFIG = {
    "dbname": "Shrijan_Attendance",
    "user": "postgres",
    "password": "asusadmin",
    "host": "localhost",
    "port": "5432"
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ---------- Data / constants (unchanged) ----------
def fetch_teachers_from_db():
    """Fetch teachers' name, email, password_hash, and teacher_id from the database."""
    teachers = {}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT teacher_id, name, email, password_hash FROM Teachers")
                for teacher_id, name, email, password_hash in cur.fetchall():
                    teachers[name] = (email, password_hash, teacher_id)
    except Exception as e:
        print(f"Error fetching teachers: {e}")
    return teachers


TEACHER_CREDENTIALS = fetch_teachers_from_db()
# print(TEACHER_CREDENTIALS)
EXPECTED_WIFI = "Shivom_5G"
# CSV_FILE = "attendance.csv"

def fetch_students_from_db():
    """Fetch students' email, name, and password_hash from the database."""
    students = {}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT student_id, name, email, password_hash FROM Students")
                for student_id, name, email, password_hash in cur.fetchall():
                    students[email] = (name, password_hash, student_id)
    except Exception as e:
        print(f"Error fetching students: {e}")
    return students

students = fetch_students_from_db()
# print(students)

# SUBJECTS = ["DMS", "COA", "TOC", "DBMS", "OOPSJ", "LMP-2", "LOOPSJ", "LCOA", "LDBMS"]

def fetch_subject_id_from_ongoing_classes():
    """Fetch the single subject_id from Ongoing_classes table."""
    subject_id = None
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT subject_id FROM Ongoing_classes LIMIT 1")
                result = cur.fetchone()
                if result:
                    subject_id = result[0]
    except Exception as e:
        print(f"Error fetching subject_id: {e}")
    return subject_id

subjects = fetch_subject_id_from_ongoing_classes()
# print(subjects)


def get_wifi_ssid():
    """Get current WiFi SSID on Windows"""
    try:
        command = ["netsh", "wlan", "show", "interfaces"]
        result = subprocess.run(command,
                               capture_output=True,
                               text=True,
                               shell=False,
                               encoding='utf-8')

        if result.returncode != 0:
            print(f"Command failed with error: {result.stderr}")
            return None

        # Look for SSID in output (handle possible extra spaces and case sensitivity)
        ssid_found = False
        for line in result.stdout.split('\n'):
            line = line.strip()
            # Match 'SSID' but not 'BSSID'
            if re.match(r"^SSID\s*:", line, re.IGNORECASE) and "bssid" not in line.lower():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    ssid = parts[1].strip()
                    if ssid and ssid.lower() != "ssid":
                        ssid_found = True
                        return ssid

        if not ssid_found:
            print("No WiFi connection found or SSID not available")
        return None

    except Exception as e:
        print(f"Error getting WiFi SSID: {str(e)}")
        return None


def update_attendance(student_name, subject):
    """Mark attendance in PostgreSQL database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get student_id
                cur.execute("SELECT student_id FROM Students WHERE name = %s", (student_name,))
                student_result = cur.fetchone()
                if not student_result:
                    return False
                student_id = student_result[0]

                # Get active session for the class
                cur.execute("""
                    SELECT s.session_id 
                    FROM Sessions s
                    JOIN Classes c ON s.class_id = c.class_id
                    WHERE c.class_name = %s AND s.is_active = TRUE
                    AND NOW() BETWEEN s.start_time AND s.end_time
                """, (subject,))
                session_result = cur.fetchone()
                if not session_result:
                    return False
                session_id = session_result[0]

                # Insert attendance record
                try:
                    cur.execute("""
                        INSERT INTO Attendance (session_id, student_id, marked_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                    """, (session_id, student_id))
                    conn.commit()
                    return True
                except psycopg2.IntegrityError:
                    # Attendance already marked
                    return False
    except Exception as e:
        print(f"Error marking attendance: {e}")
        return False


# attendance view by student 
def get_student_attendance(student_name):
    """Get attendance summary for a student"""
    for key,value in students.items():
        if value[0]==student_name:
            student_id=value[2]
            break
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        s.subject_name,
                        COUNT(a.attendance_id) AS present,
                        COALESCE(
                            ROUND((COUNT(a.attendance_id)::decimal / NULLIF(s.total_classes_held, 0)) * 100, 2),
                            0
                        ) AS percentage
                    FROM Subjects s
                    LEFT JOIN Attendance a 
                        ON s.subject_id = a.subject_id 
                        AND a.student_id = %s
                    GROUP BY s.subject_name, s.total_classes_held
                    ORDER BY s.subject_name;
                """, (student_id,))
                return cur.fetchall()
    except Exception as e:
        print(f"Error getting attendance: {e}")
        return []


# attendance view by teacher 
def get_all_attendance():
    """Get attendance for all students"""
    subjects = fetch_subject_id_from_ongoing_classes()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        s.name AS student_name,
                        COUNT(a.attendance_id) AS total_classes_attended,
                        COALESCE(
                            ROUND((COUNT(a.attendance_id)::decimal / NULLIF(sub.total_classes_held, 0)) * 100, 2), 
                            0
                        ) AS attendance_percentage
                        FROM Students s
                        LEFT JOIN Attendance a 
                        ON s.student_id = a.student_id 
                        AND a.subject_id = %s   
                        JOIN Subjects sub
                        ON sub.subject_id = %s  
                        GROUP BY s.student_id, s.name, sub.total_classes_held
                        ORDER BY s.name;
                """, (subjects,subjects, ))
                return cur.fetchall()
    except Exception as e:
        print(f"Error getting all attendance: {e}")
        return []

# def ensure_attendance_csv():
#     """Create CSV with zeroed subjects if missing (unchanged behavior)."""
#     if not os.path.exists(CSV_FILE):
#         data = []
#         for sid, (name, _) in students.items():
#             row = {"Name": name}
#             for subj in SUBJECTS:
#                 row[subj] = 0
#             data.append(row)
#         df = pd.DataFrame(data)
#         df.to_csv(CSV_FILE, index=False)
#         print("Created new attendance.csv")