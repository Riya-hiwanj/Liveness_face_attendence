import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://livenessfaceattendence-default-rtdb.firebaseio.com/"
})

ref = db.reference('Employees')

data = {
    "emp_101":
        {
            "name": "Abhishek Pawar",
            "job_position": "MLops Engineer",
            "starting_year": 2020,
            "total_attendance": 1,
            "email": "abhishek.pawar@mitaoe.ac.in",
            "last_attendance_time": "2023-03-30 00:54:34"
        },
    "emp_102":
        {
            "name": "Riya Hiwanj",
            "job_position": "Data Scientist",
            "starting_year": 2021,
            "total_attendance": 0,
            "email": "riya.hiwanj@mitaoe.ac.in",
            "last_attendance_time": "2023-03-29 00:53:00"
        },
    "emp_103":
        {
            "name": "Sarthak Jamdar",
            "job_position": "AI Engineer",
            "starting_year": 2019,
            "total_attendance": 3,
            "email": "sarthak.jamdar@mitaoe.ac.in",
            "last_attendance_time": "2023-02-22 00:54:34"
        }
}

for key, value in data.items():
    ref.child(key).set(value)