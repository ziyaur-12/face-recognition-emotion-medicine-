import os
from tkinter import ttk
import os
import cv2
import face_recognition
import numpy as np
import csv
import pickle
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from tensorflow.keras.models import model_from_json
import threading
from tkinter import *
# from sklearn import metrics  # Not used in this file
from PIL import Image, ImageTk

# Define the Emotion Detection Model
def FacialExpressionModel(json_file, weights_file):
    with open(json_file, "r") as file:
        loaded_model_json = file.read()
        model = model_from_json(loaded_model_json)
    model.load_weights(weights_file)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

# Initialize Emotion Detector
emotion_model = FacialExpressionModel("model_a1.json", "model_weights1.h5")
facec = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
EMOTIONS_LIST = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise", "Mohd_Asrar"]

# Initialize Face Recognition System
def findEncodings(images, progress_callback):
    encodeList = []
    total_images = len(images)
    
    for i, img in enumerate(images):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)
        if encode:
            encodeList.append(encode[0])
        # Update progress
        progress_callback(i + 1, total_images)
    
    return encodeList

# Define Face Recognition Functions
def process_images_thread():
    global path, save_path
    if not path:
        messagebox.showerror("Error", "No folder selected.")
        return

    if not save_path:
        messagebox.showerror("Error", "No save location selected.")
        return

    progress_var.set("Loading images...")
    root.update_idletasks()

    images = []
    classNames = []
    myList = os.listdir(path)

    for cls in myList:
        curImg = cv2.imread(f'{path}/{cls}')
        if curImg is not None:
            images.append(curImg)
            classNames.append(os.path.splitext(cls)[0])

    progress_var.set("Generating encodings...")
    root.update_idletasks()

    encodings = findEncodings(images, update_progress)

    progress_var.set("Saving encodings...")
    root.update_idletasks()

    with open(save_path, 'wb') as f:
        pickle.dump((encodings, classNames), f)

    progress_var.set("Completed!")
    messagebox.showinfo("Success", f"Encodings saved to {save_path}")
def process_images():
    threading.Thread(target=process_images_thread).start()

def update_progress(current, total):
    progress = (current / total) * 100
    progress_var.set(f"Processing: {current}/{total} ({progress:.2f}%)")

def select_folder():
    global path
    path = filedialog.askdirectory(title="Select Image Folder")
    folder_label.config(text=f"Selected folder: {path}")

def select_save_path():
    global save_path
    save_path = filedialog.asksaveasfilename(defaultextension=".pkl", filetypes=[("Pickle Files", "*.pkl")], title="Select Save Location")
    save_label.config(text=f"Save location: {save_path}")

#Emotion detection
def detect_emotion(file_path):
    image = cv2.imread(file_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = facec.detectMultiScale(gray_image, 1.3, 5)
    try:
        for (x, y, w, h) in faces:
            fc = gray_image[y:y+h, x:x+w]
            roi = cv2.resize(fc, (48, 48))
            pred = EMOTIONS_LIST[np.argmax(emotion_model.predict(roi[np.newaxis, :, :, np.newaxis]))]
        label1.configure(foreground="#011638", text=pred)
    except:
        label1.configure(foreground="#011638", text="Unable to detect")

def show_detect_button(file_path):
    detect_b = Button(top, text="Detect Emotion", command=lambda: detect_emotion(file_path), padx=10, pady=5)
    detect_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
    detect_b.place(relx=0.15, rely=0.06)

def upload_image():
    try:
        file_path = filedialog.askopenfilename()
        uploaded = Image.open(file_path)
        uploaded.thumbnail(((top.winfo_width()/2.25), (top.winfo_height()/2.25)))
        im = ImageTk.PhotoImage(uploaded)

        sign_image.configure(image=im)
        sign_image.image = im
        label1.configure(text='')
        show_detect_button(file_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))


def select_pkl_file():
    global pkl_path
    pkl_path = filedialog.askopenfilename(defaultextension=".pkl", filetypes=[("Pickle Files", "*.pkl")], title="Select .pkl File")
    pkl_file_label.config(text=f"Selected .pkl file: {pkl_path}")
    load_encodings()

def load_encodings():
    global encodeListKnown, classNames
    try:
        with open(pkl_path, 'rb') as f:
            encodeListKnown, classNames = pickle.load(f)
    except FileNotFoundError:
        messagebox.showerror("Error", "Encoding file not found. Please generate encodings first.")
        encodeListKnown, classNames = [], []

def detect_faces_live():
    cap = cv2.VideoCapture(0)  # Use the default camera
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image")
            break

        # Resize the image for processing
        img = cv2.resize(img, (100, 60))  # Resize the frame for quicker processing
        face_locations = face_recognition.face_locations(img)
        encodings = face_recognition.face_encodings(img, face_locations)

        for (top, right, bottom, left), encode_face in zip(face_locations, encodings):
            matches = face_recognition.compare_faces(encodeListKnown, encode_face)
            faceDis = face_recognition.face_distance(encodeListKnown, encode_face)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                color = (0, 255, 0)  # Green for recognized faces
            else:
                name = "Unknown"
                color = (0, 0, 255)  # Red for unknown faces

            # Draw rectangle around face
            cv2.rectangle(img, (left, top), (right, bottom), color, 2)
            cv2.rectangle(img, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(img, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)

            # Mark attendance for recognized faces
            if name != "Unknown":
                markAttendance(name)

        # Convert the image to RGB for display
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imshow('Live Face Detection', rgb_img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print('Exited...')
            break

    cap.release()
    cv2.destroyAllWindows()


def detect_faces_image():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    img = cv2.imread(file_path)
    if img is None:
        messagebox.showerror("Error", "Failed to load image.")
        return

    img = resize_image(img, width=800)  # Resize the image to a consistent width

    face_locations = face_recognition.face_locations(img)
    encodings = face_recognition.face_encodings(img, face_locations)

    for (top, right, bottom, left), encode_face in zip(face_locations, encodings):
        matches = face_recognition.compare_faces(encodeListKnown, encode_face)
        faceDis = face_recognition.face_distance(encodeListKnown, encode_face)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
            markAttendance(name)
        else:
            markUnknownFace()
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, "Unknown", (left + 6, bottom - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

    display_result(img)

def resize_image(image, width):
    (h, w) = image.shape[:2]
    aspect_ratio = width / float(w)
    new_height = int(h * aspect_ratio)
    resized_image = cv2.resize(image, (width, new_height))
    return resized_image

def markAttendance(name):
    now = datetime.now()
    dtString = now.strftime('%Y-%m-%d %H:%M:%S')
    dayString = now.strftime('%A')
    try:
        with open('KnownFaces.csv', 'r+', newline='') as f:
            existing_entries = f.read().splitlines()
            if any(name.lower() in entry.lower() for entry in existing_entries):
                print(f'{name.upper()} is already present.')
            else:
                f.write(f'\n{name},{dtString},{dayString}')
                print(f'{name.upper()} present.')
    except FileNotFoundError:
        with open('KnownFaces.csv', 'w', newline='') as f:
            f.write(f'{name},{dtString},{dayString}')
            print(f'{name.upper()} present.')

def markUnknownFace():
    now = datetime.now()
    dtString = now.strftime('%Y-%m-%d %H:%M:%S')
    dayString = now.strftime('%A')
    try:
        with open('UnknownFaces.csv', 'a', newline='') as f:
            f.write(f'Unknown,{dtString},{dayString}\n')
            print('Unknown face detected and marked.')
    except FileNotFoundError:
        with open('UnknownFaces.csv', 'w', newline='') as f:
            f.write(f'Unknown,{dtString},{dayString}\n')
            print('Unknown face detected and marked.')

def display_result(image):
    # Resize the image to a smaller resolution before displaying
    resized_image = resize_image(image, width=400)  # Set a width for the display
    cv2.imshow('Result', resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def resize_image(image, width):
    (h, w) = image.shape[:2]
    aspect_ratio = width / float(w)
    new_height = int(h * aspect_ratio)
    resized_image = cv2.resize(image, (width, new_height))
    return resized_image


# Create the main window
root = tk.Tk()
root.title("Emotion Detection and Face Recognition")

#***************
path = ""
save_path = ""
#***************

# Set up GUI elements
top = tk.Frame(root, width=1000, height=800, bg="#eeeeee")
top.pack(padx=20, pady=20)


#Emotion detection*******************

label2 = Label(top, text='EMOTION DETECTION', font=('arial', 15, 'bold'))
label2.place(relx=0.0, rely=0.0)

upload_b = Button(top, text="Upload Image", command=upload_image, padx=10, pady=5)
upload_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
upload_b.place(relx=0.0, rely=0.06)

label1 = Label(top, text='', font=('arial', 15, 'bold'))
label1.place(relx=0.3, rely=0.06)

sign_image = Label(top)
sign_image.place(relx=0.34, rely=0.2)
#Traind image

label2 = Label(top, text='TRAIN IMAGES', font=('arial', 15, 'bold'))
label2.place(relx=0.0, rely=0.14)

folder_b = tk.Button(top, text="Train Image Folder", command=select_folder, padx=10, pady=5)
folder_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
folder_b.place(relx=0.00, rely=0.20)
# folder_label = Label(top, text="Selected folder: None")
# folder_label.place(relx=0.25, rely=0.20)
folder_label = Label()

save_b = Button(top, text="Save train (.pkl)", command=select_save_path, padx=10, pady=5)
save_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
save_b.place(relx=0.17, rely=0.20)
# save_label = Label(top, text="Save location: None")
# save_label.place(relx=0.25, rely=0.66)
save_label = Label()

process_button = tk.Button(root, text="Generate .pkl", command=process_images,padx=10, pady=5)
process_button.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
process_button.place(relx=0.02, rely=0.28)
progress_var = tk.StringVar()
progress_label = Label(top, textvariable=progress_var)
progress_label.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
progress_label.place(relx=0.15, rely=0.28)

#Face recognition

label2 = Label(top, text='FACE DETECTION', font=('arial', 15, 'bold'))
label2.place(relx=0.0, rely=0.34)

pkl_b = Button(top, text="Select .pkl File", command=select_pkl_file, padx=10, pady=5)
pkl_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
pkl_b.place(relx=0.0, rely=0.40)
# pkl_file_label = Label(top, text="Selected .pkl file: None")
# pkl_file_label.place(relx=0.25, rely=0.70)
pkl_file_label = Label()

detect_b = Button(top, text="Detect Faces in Image", command=detect_faces_image, padx=10, pady=5)
detect_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
detect_b.place(relx=0.0, rely=0.46)

live_b = Button(top, text="Detect Faces Live", command=lambda: threading.Thread(target=detect_faces_live, daemon=True).start(), padx=10, pady=5)
live_b.configure(background="#364156", foreground='white', font=('arial', 10, 'bold'))
live_b.place(relx=0.18, rely=0.46)


label2 = Label(top, text='Developer : Mohd Asrar', font=('arial', 15, 'bold'))
label2.place(relx=0.35, rely=0.9)
label3 = Label(top, text='Everything will be easy when you will start.', font=('arial', 15, 'bold'))
label3.place(relx=0.25, rely=0.85)

root.mainloop()