import os
import pickle
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
from datetime import datetime
from tensorflow.keras.models import model_from_json
import requests
import json
from geopy.distance import geodesic
from geopy import Point

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://livenessfaceattendence-default-rtdb.firebaseio.com/",
    'storageBucket': "livenessfaceattendence.appspot.com"
})

bucket = storage.bucket()

#Importing the mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
print(len(imgModeList))

# Load the encoding file
print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, employeeid = encodeListKnownWithIds
# print(employeeid)
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgEmployee = []

# Load Face Detection Model
face_cascade = cv2.CascadeClassifier("models/haarcascade_frontalface_default.xml")


# Load Anti-Spoofing Model graph
json_file = open('antispoofing_models/antispoofing_model_mobilenet.json','r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)


# load antispoofing model weights
model.load_weights('antispoofing_models/antispoofing_model_40-0.995714.h5')
print("Model loaded from disk")

count =0

cap = cv2.VideoCapture(0)
cap.set(3, 680)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background2.png')


#geofencing

flag = False

api_key = "9c433b72eeb618cef0e896b9646523da"
url = f"http://api.ipstack.com/check?access_key={api_key}"
response = requests.get(url)
data = json.loads(response.text)
latitude = data['latitude']
longitude = data['longitude']

# Define the center point of the geofence and its radius in meters
geofence_center = Point(18.67340033569336, 73.88949993896484) #18.674755, 73.892306
geofence_radius = 1000 # in meters

# Define the user's current location
user_location = Point(latitude, longitude)

# Calculate the distance between the user's location and the center of the geofence
distance_to_center = geodesic(user_location, geofence_center).meters
print(distance_to_center)
# Check if the user is inside the geofence
if distance_to_center <= geofence_radius:
    flag=True
else:
    success, img = cap.read()
    cv2.imshow("Face Attendance", imgBackground)
    key = cv2.waitKey(0)
    print("User is outside the geofence")


while flag:
    try:
        success, img = cap.read()

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        for (x, y, w, h) in faces:
            face = img[y - 5:y + h + 5, x - 5:x + w + 5]
            resized_face = cv2.resize(face, (160, 160))
            resized_face = resized_face.astype("float") / 255.0
            # resized_face = img_to_array(resized_face)
            resized_face = np.expand_dims(resized_face, axis=0)
            # pass the face ROI through the trained liveness detector
            # model to determine if the face is "real" or "fake"
            preds = model.predict(resized_face)[0]
            print(preds)
            if preds > 0.5:
                label = 'spoof'
                # cv2.putText(img, label, (x, y - 10),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                # cv2.rectangle(img, (x, y), (x + w, y + h),
                #               (0, 0, 255), 2)
                count =0
                if faceCurFrame:
                    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                        print("matches", matches)
                        print("faceDis", faceDis)

                        matchIndex = np.argmin(faceDis)
                        print("Match Index", matchIndex)
                        #
                        # if matches[matchIndex] == None:
                        #     continue
                        if matches[matchIndex]:
                            # print("Known Face Detected")
                            #print(employeeid[matchIndex])
                            y1, x2, y2, x1 = faceLoc
                            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                            if counter == 0:
                                cvzone.putTextRect(imgBackground, "spoof", (275, 400))
                                cv2.imshow("Face Attendance", imgBackground)
                                cv2.waitKey(1)
                else:
                    modeType = 0
                    counter = 0
            else:
                label = 'real'
                cv2.putText(img, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.rectangle(img, (x, y), (x + w, y + h),
                              (0, 255, 0), 2)
                count += 1
                if faceCurFrame:
                    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                        print("matches", matches)
                        print("faceDis", faceDis)

                        matchIndex = np.argmin(faceDis)
                        if matches[matchIndex]:
                            # print("Known Face Detected")
                            # print(employeeid[matchIndex])
                            y1, x2, y2, x1 = faceLoc
                            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                            id = employeeid[matchIndex]
                            if counter == 0:
                                cvzone.putTextRect(imgBackground, "Real", (275, 400))
                                cv2.imshow("Face Attendance", imgBackground)
                                cv2.waitKey(1)
                                if(count > 15) and (faceDis[matchIndex] < 0.45):
                                    counter = 1
                                    modeType = 1
                                    count=0

                    if counter != 0:

                        if counter == 1:
                            # Get the Data
                            employeeInfo = db.reference(f'Employees/{id}').get()
                            print(employeeInfo)
                            # Get the Image from the storage
                            blob = bucket.get_blob(f'images/{id}.png')
                            array = np.frombuffer(blob.download_as_string(), np.uint8)
                            imgEmployee = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                            # Update data of attendance
                            datetimeObject = datetime.strptime(employeeInfo['last_attendance_time'],
                                                               "%Y-%m-%d %H:%M:%S")
                            secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                            print(secondsElapsed)
                            if secondsElapsed > 100:
                                ref = db.reference(f'Employees/{id}')
                                employeeInfo['total_attendance'] += 1
                                ref.child('total_attendance').set(employeeInfo['total_attendance'])
                                ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            else:
                                modeType = 3
                                counter = 0
                                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                        if modeType != 3:

                            if 15 < counter < 40:
                                modeType = 2

                            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                            if counter <= 10:
                                cv2.putText(imgBackground, str(employeeInfo['total_attendance']), (861, 125),
                                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                                cv2.putText(imgBackground, str(employeeInfo['job_position']), (1006, 550),
                                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                                cv2.putText(imgBackground, str(id), (1006, 493),
                                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                                cv2.putText(imgBackground, str(employeeInfo['email']), (1025, 625),
                                            cv2.FONT_HERSHEY_COMPLEX, 0.4, (100, 100, 100), 1)
                                cv2.putText(imgBackground, str(employeeInfo['starting_year']), (1125, 625),
                                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                                (w, h), _ = cv2.getTextSize(employeeInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                                offset = (414 - w) // 2
                                cv2.putText(imgBackground, str(employeeInfo['name']), (808 + offset, 445),
                                            cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                                imgBackground[175:175 + 216, 909:909 + 216] = imgEmployee

                            counter += 1

                            if counter >= 35:
                                counter = 0
                                modeType = 0
                                employeeInfo = []
                                imgEmployee = []
                                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                else:
                    modeType = 0
                    counter = 0

        #cv2.imshow("Webcam", img)
        cv2.imshow("Face Attendance", imgBackground)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    except Exception as e:
        print(e)
        pass
