import cv2
import json
import numpy as np
import time
import mediapipe as mp
from db_config import get_connection

# ── MediaPipe Face Detection + Simple Encoding ────────────────────────────────
mp_face_detection = mp.solutions.face_detection
mp_face_mesh      = mp.solutions.face_mesh
mp_drawing        = mp.solutions.drawing_utils

print("[INFO] Loading face models...")
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.7)
face_mesh      = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,
                                        refine_landmarks=True, min_detection_confidence=0.7)
print("[INFO] Models loaded successfully.")


def get_face_encoding(frame_bgr):
    """
    Extract a 1404-point landmark encoding from face using MediaPipe FaceMesh.
    Returns (encoding_array, face_count)
    """
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return None, 0

    if len(results.multi_face_landmarks) > 1:
        return None, len(results.multi_face_landmarks)

    # Flatten all 468 landmark (x, y, z) coords into a 1404-length vector
    landmarks = results.multi_face_landmarks[0].landmark
    encoding  = np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten()
    return encoding, 1


def capture_face_encoding():
    print("\n[INFO] Camera opening... Look straight at the camera. Press SPACE to capture.")

    cap = cv2.VideoCapture(0)
    time.sleep(1)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        return None

    encoding = None

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[ERROR] Cannot read frame.")
            break

        frame   = cv2.resize(frame, (640, 480))
        display = frame.copy()

        # Show live face detection feedback
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        det_res = face_detection.process(rgb)

        if det_res.detections:
            for detection in det_res.detections:
                bboxC = detection.location_data.relative_bounding_box
                h, w  = frame.shape[:2]
                x1 = int(bboxC.xmin * w)
                y1 = int(bboxC.ymin * h)
                x2 = x1 + int(bboxC.width * w)
                y2 = y1 + int(bboxC.height * h)
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display, "Face detected! Press SPACE to capture",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        else:
            cv2.putText(display, "No face detected - look at camera",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        cv2.putText(display, "Press Q to cancel",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
        cv2.imshow("Employee Registration", display)

        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE
            print("[INFO] Processing face...")
            enc, count = get_face_encoding(frame)

            if count == 0:
                print("[WARNING] No face detected. Please try again.")
            elif count > 1:
                print("[WARNING] Multiple faces detected. One person only.")
            else:
                encoding = enc
                print("[SUCCESS] Face captured successfully!")
                break

        elif key == ord('q'):
            print("[INFO] Registration cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return encoding


def register_employee():
    print("\n===== ADMIN: REGISTER NEW EMPLOYEE =====")
    full_name  = input("Full Name       : ").strip()
    id_number  = input("ID Number       : ").strip()
    department = input("Department      : ").strip()
    company_id = input("Company ID      : ").strip()

    if not all([full_name, id_number, department, company_id]):
        print("[ERROR] All fields are required.")
        return

    print("\nCapturing face data...")
    encoding = capture_face_encoding()

    if encoding is None:
        print("[ERROR] Face capture failed. Employee not registered.")
        return

    encoding_json = json.dumps(encoding.tolist())

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Employees WHERE IDNumber = ?", (id_number,))
        if cursor.fetchone()[0] > 0:
            print(f"[ERROR] ID Number '{id_number}' already exists.")
            conn.close()
            return

        cursor.execute("""
            INSERT INTO Employees (CompanyID, FullName, IDNumber, Department, FaceEncoding)
            VALUES (?, ?, ?, ?, ?)
        """, (company_id, full_name, id_number, department, encoding_json))

        conn.commit()
        conn.close()
        print(f"\n[SUCCESS] Employee '{full_name}' registered successfully!")

    except Exception as e:
        print(f"[ERROR] Database error: {e}")


if __name__ == "__main__":
    while True:
        register_employee()
        again = input("\nRegister another employee? (y/n): ").lower()
        if again != 'y':
            print("[INFO] Exiting. Goodbye!")
            break