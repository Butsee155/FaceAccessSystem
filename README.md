# 🔐 Face Access System

> A real-time face recognition-based employee access control system built with Python, MediaPipe, and SQL Server.

## 📌 Overview

The **Face Access System** is a desktop application that uses real-time face recognition to verify employee identities and control access to secured areas. Administrators can register employees with face scan data, and the access terminal automatically identifies individuals and logs every access attempt.

---

## ✨ Features

- 🔐 **Secure Login** — Role-based login for Admin and Access Terminal
- 📊 **Admin Dashboard** — Live stats: total employees, access granted/denied today
- 👥 **Employee Management** — Add, view, search, and delete employees
- 📷 **Face Registration** — Capture and store face encodings via webcam
- 🖥️ **Live Access Terminal** — Real-time face scanning with embedded camera feed
- 📋 **Access Logs** — Full history of every access attempt with timestamps
- 📤 **Export Reports** — Export employees and logs to Excel (.xlsx) or CSV

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| Face Recognition | MediaPipe 0.10.9 (468-point FaceMesh) |
| GUI Framework | Tkinter (Corporate Blue theme) |
| Database | Microsoft SQL Server 2019 + SSMS 20 |
| DB Connector | pyodbc |
| Export | openpyxl, csv |
| Image Processing | OpenCV, Pillow, NumPy |

---

## 📁 Project Structure

```
FaceAccessSystem/
│
├── main_app.py              # Login screen & launcher
├── admin_panel.py           # Admin dashboard (employees, logs, export)
├── access_terminal_gui.py   # Live face scan terminal with GUI
├── admin_register.py        # CLI employee registration (legacy)
├── access_terminal.py       # CLI access terminal (legacy)
├── db_config.py             # SQL Server database connection
└── README.md
```

---

## 🗄️ Database Schema

```sql
-- Employees Table
CREATE TABLE Employees (
    EmployeeID      INT IDENTITY(1,1) PRIMARY KEY,
    CompanyID       VARCHAR(50) NOT NULL,
    FullName        VARCHAR(100) NOT NULL,
    IDNumber        VARCHAR(50) NOT NULL UNIQUE,
    Department      VARCHAR(100) NOT NULL,
    RegisteredDate  DATETIME DEFAULT GETDATE(),
    FaceEncoding    TEXT NOT NULL
);

-- Access Logs Table
CREATE TABLE AccessLogs (
    LogID           INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID      INT FOREIGN KEY REFERENCES Employees(EmployeeID),
    AccessTime      DATETIME DEFAULT GETDATE(),
    AccessGranted   BIT NOT NULL
);
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10 — [python.org](https://python.org)
- SQL Server 2019 Express — [Microsoft](https://www.microsoft.com/en-us/sql-server/sql-server-downloads)
- SSMS 20 — [Microsoft](https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms)
- ODBC Driver 17 for SQL Server — [Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/FaceAccessSystem.git
cd FaceAccessSystem
```

### 3. Install Dependencies
```bash
pip install mediapipe==0.10.9 opencv-python numpy pyodbc pillow openpyxl
```

### 4. Set Up the Database
Open SSMS and run the SQL script in `database/setup.sql` to create the database and tables.

### 5. Configure Database Connection
Edit `db_config.py`:
```python
def get_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost\\SQLEXPRESS;'
        'DATABASE=FaceAccessSystem;'
        'Trusted_Connection=yes;'
    )
    return conn
```

### 6. Run the Application
```bash
py -3.10 main_app.py
```

> Default admin password: `admin123`  
> Change it in `main_app.py` → `ADMIN_PASSWORD = "your_password"`

---

## 🚀 How It Works

1. **Admin registers an employee** — enters details + captures face via webcam
2. **Face encoding** (1404 MediaPipe landmark points) is stored as JSON in SQL Server
3. **Access terminal** scans faces in real-time and compares encodings
4. **If matched** — employee info is displayed and access is granted
5. **If unknown** — access is denied and logged
6. **All events** are recorded in `AccessLogs` with timestamp

---

## ⚠️ Known Challenges & Solutions

| Challenge | Solution |
|---|---|
| `dlib` failed to build on Windows | Switched to **MediaPipe** (no compilation needed) |
| `face_recognition` RuntimeError on uint8 images | Bypassed wrapper, used MediaPipe FaceMesh directly |
| `CAP_DSHOW` camera backend error | Used `cv2.CAP_ANY` with auto-detection fallback |
| mediapipe `solutions` attribute missing | Pinned to `mediapipe==0.10.9` |

---

## 📸 Screenshots

> _Add your screenshots here_

| Login Screen | Admin Dashboard |
|---|---|
| ![Login](screenshots/login.png) | ![Dashboard](screenshots/dashboard.png) |

| Access Terminal | Export Reports |
|---|---|
| ![Terminal](screenshots/terminal.png) | ![Export](screenshots/export.png) |

---

## 🔮 Future Improvements

- [ ] Email alerts on denied access
- [ ] Sound notifications (granted/denied)
- [ ] Photo snapshot saved on each access attempt
- [ ] Employee ID card PDF generation
- [ ] Web-based version using Flask
- [ ] Multiple camera support
- [ ] Shift & working hours tracking

---

## 👤 Author

**R.M. Nisitha Nethsilu**  
🔗 [LinkedIn]  - www.linkedin.com/in/nisithanethsilu/
🐙 [GitHub] - www.github.com/Butsee155

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

> ⭐ If you found this project helpful, please give it a star on GitHub!
