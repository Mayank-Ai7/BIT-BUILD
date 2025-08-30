-- ======================================================
-- ERP Attendance Database Schema
-- ======================================================

-- ---------- 1. Teachers ----------
CREATE TABLE Teachers (
    teacher_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- ---------- 2. Students ----------
CREATE TABLE Students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- ---------- 3. Classes ----------
CREATE TABLE Subjects (
    subject_id SERIAL PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    teacher_id INT NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES Teachers(teacher_id)
);

-- ---------- 4. Ongoing_classes (Timestamp <-> Classes) ----------
CREATE TABLE Ongoing_classes (
	ongoing_class_id SERIAL PRIMARY KEY,
	subject_id INT NOT NULL,
	total_class_completed INT,
	marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
);

-- ---------- 5. Attendance ----------
CREATE TABLE Attendance (
    attendance_id SERIAL PRIMARY KEY,
    subject_id INT NOT NULL,
    student_id INT NOT NULL,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);


-- ======================================================
-- SAMPLE QUERIES
-- ======================================================
/*
-- 1. Teacher: View attendance for a class
-- Shows each student and whether attended in a given session
SELECT s.name, a.session_id, a.marked_at
FROM Students s
JOIN Attendance a ON s.student_id = a.student_id
JOIN Sessions se ON a.session_id = se.session_id
WHERE se.class_id = 1;

-- 2. Student: View own attendance across subjects
SELECT c.class_name, COUNT(a.attendance_id) AS attended_classes
FROM Classes c
JOIN Sessions se ON c.class_id = se.class_id
LEFT JOIN Attendance a ON se.session_id = a.session_id AND a.student_id = 1
GROUP BY c.class_id, c.class_name;

-- 3. Mark attendance (validates QR + expiry)
INSERT INTO Attendance (session_id, student_id)
SELECT se.session_id, 1
FROM Sessions se
WHERE se.qr_token = 'xyz123'
  AND NOW() BETWEEN se.start_time AND se.end_time
  AND se.is_active = TRUE;
  */

-- (If the above insert fails = invalid or expired QR)



-- QUERY FOR UPDATING THE ONGOING_CLASSES TABLE 
1.
/*
SELECT total_class_completed FROM Ongoing_classes 
'INSERT INTO Ongoing_classes (subject_id, total_class_completed, marked_at) 
   VALUES ($1, $2, CURRENT_TIMESTAMP)' ,
   [req.user.subject_id, totalCompleted + 1]
   */

   await db.query(
  "UPDATE Ongoing_classes SET subject_id = $1, total_class_completed = total_class_completed + 1, marked_at = CURRENT_TIMESTAMP",
  [newSubjectId]
);




-- MARKING ATTENDANCE BY SCANNING QR_CODE
2.

/*
const query = `
  INSERT INTO Attendance (subject_id, student_id, marked_at)
  SELECT $1, $2, NOW()
  FROM Ongoing_classes oc
  WHERE oc.subject_id = $1
    AND NOW() BETWEEN oc.marked_at AND oc.marked_at + INTERVAL '1 hour';
`;

await db.query(query, [subjectId, studentId]);
*/

INSERT INTO Attendance (subject_id, student_id, marked_at)
SELECT 2, 4, NOW()
FROM Ongoing_classes oc
WHERE oc.subject_id = 2
  AND NOW() BETWEEN oc.marked_at AND oc.marked_at + INTERVAL '1 hour';


FOR VIEWING THE ATTENDANCE AS A STUDENT
  3.
SELECT 
    s.subject_name,
    s.total_classes_held,
    COUNT(a.attendance_id) AS classes_attended
FROM Subjects s
LEFT JOIN Attendance a 
    ON s.subject_id = a.subject_id AND a.student_id = 1
GROUP BY s.subject_name, s.total_classes_held
ORDER BY s.subject_name;




4.
INSERT INTO Students (name, email, password_hash) VALUES
('Arin Soni', 'arin@gmail.com', '2twsf4tq2'),
('Ayush Verma', 'ayush@gmail.com', 'sef321dg'),
('Mayank Banjare', 'mayank@gmail.com', 'df32f3dd'),
('Shrijan Patel', 'shrijan@gmail.com', '890sj02j');

5.
INSERT INTO Teachers (name, email, password_hash) VALUES
('Ani Thomas', 'ani@gmail.com', 'swf22133r'),
('Sumita Nair', 'sumita@gmail.com', 'ad32d233r'),
('Sanjay Sharma', 'sanjay@gmail.com', 'duh8928hs');

6.
INSERT INTO subjects (subject_id, subject_name, teacher_id, total_classes_held) VALUES
(1, 'TOC', 1, 0),
(2, 'Chemistry', 2, 1),
(3, 'DMS', 3, 1),
(4, 'AM', 3, 0);

7.
-- GENERATING QR INCREMENTS THE total_classes_held BY 1
UPDATE Subjects
SET total_classes_held = total_classes_held + 1
WHERE subject_id = 1;  -- replace 1 with your subject_id


8.
-- FOR VIEWING THE ATTENDANCE AS A TEACHER

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
    AND a.subject_id = 4   -- teacher's subject_id
    JOIN Subjects sub
    ON sub.subject_id = 4   -- same subject_id, gives total_classes_held
    GROUP BY s.student_id, s.name, sub.total_classes_held
    ORDER BY s.name;

