import cv2
import json
import numpy as np
import time
import mediapipe as mp
from db_config import get_connection
from datetime import datetime

mp_face_detection = mp.solutions.face_detection
mp_face_mesh      = mp.solutions.face_mesh

print("[INFO] Loading models...")
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.7)
face_mesh      = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                        refine_landmarks=True, min_detection_confidence=0.7)
print("[INFO] Models ready.")

MATCH_THRESHOLD = 0.035  # lower = stricter


def get_face_encoding(frame_bgr):
    rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None
    landmarks = results.multi_face_landmarks[0].landmark
    return np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten()


def load_employees():
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT EmployeeID, FullName, IDNumber, Department, CompanyID, RegisteredDate, FaceEncoding FROM Employees")
    rows   = cursor.fetchall()
    conn.close()
    employees = []
    for row in rows:
        enc = np.array(json.loads(row[6]))
        employees.append({
            "id": row[0], "full_name": row[1], "id_number": row[2],
            "department": row[3], "company_id": row[4],
            "registered_date": row[5], "encoding": enc
        })
    print(f"[INFO] {len(employees)} employee(s) loaded.")
    return employees


def log_access(employee_id, granted):
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO AccessLogs (EmployeeID, AccessGranted) VALUES (?, ?)",
                       (employee_id, 1 if granted else 0))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Log failed: {e}")


def run_terminal():
    employees = load_employees()
    cap       = cv2.VideoCapture(0)
    time.sleep(1)

    last_log_time = {}  # prevent duplicate logs within 5 seconds

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame   = cv2.resize(frame, (640, 480))
        display = frame.copy()
        now     = datetime.now()

        encoding = get_face_encoding(frame)

        if encoding is not None and len(employees) > 0:
            distances  = [np.linalg.norm(encoding - e["encoding"]) for e in employees]
            best_idx   = np.argmin(distances)
            best_dist  = distances[best_idx]

            if best_dist < MATCH_THRESHOLD:
                emp   = employees[best_idx]
                color = (0, 255, 0)

                # Display info panel
                info = [
                    "  ACCESS GRANTED  ",
                    f"Name      : {emp['full_name']}",
                    f"ID Number : {emp['id_number']}",
                    f"Department: {emp['department']}",
                    f"Company ID: {emp['company_id']}",
                    f"Time      : {now.strftime('%H:%M:%S')}",
                    f"Date      : {now.strftime('%Y-%m-%d')}",
                ]
                y = 40
                cv2.rectangle(display, (5, 5), (400, 210), (0, 80, 0), -1)
                for line in info:
                    cv2.putText(display, line, (10, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
                    y += 28

                # Log only once per 5 seconds per employee
                last = last_log_time.get(emp["id"], 0)
                if time.time() - last > 5:
                    log_access(emp["id"], True)
                    last_log_time[emp["id"]] = time.time()
            else:
                color = (0, 0, 255)
                cv2.rectangle(display, (5, 5), (300, 60), (80, 0, 0), -1)
                cv2.putText(display, "  ACCESS DENIED - Unknown Person",
                            (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(display, "Scanning...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)

        cv2.putText(display, "Press Q to quit", (10, 465),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
        cv2.imshow("Face Access Terminal", display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_terminal()