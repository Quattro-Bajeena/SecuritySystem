from infrastructure import save_recording
from infrastructure.tempimage import TempImage

from imutils.video import VideoStream
import argparse
import warnings
import datetime
import imutils
import json
import time
import cv2

config = None
def setup():
	global config
	configuration_path = "conf.json"
	config = json.load(open(configuration_path))
	print("Loaded config", config)

	if config["use_azure"]:
		save_recording.connection_setup(config)
		

def processing_captures(frame, gray, average, last_uploaded, motion_counter, config):
	text = "Unoccupied"
	timestamp = datetime.datetime.now()

	cv2.accumulateWeighted(gray, average, config["average_strength"])
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(average))
	
	thresh = cv2.threshold(frameDelta, config["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=config["dilate_iterations"])
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)

	for c in cnts:
		if cv2.contourArea(c) < config["min_area"]:
			continue
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Occupied"

	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, f"Room Status: {text}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
	
	if text == "Occupied":
		if (timestamp - last_uploaded).seconds >= config["min_upload_seconds"]:
			motion_counter += 1
			if motion_counter >= config["min_motion_frames"]:

				if config["use_azure"]:
					save_recording.upload_image(frame)

				print("[CAPTURE]")
				last_uploaded = timestamp
				motion_counter = 0
	else:
		motion_counter = 0
	if config["show_video"]:
		cv2.imshow("Security Feed", frame)
		cv2.imshow("Thresh", thresh)
		cv2.imshow("Frame Delta", frameDelta)
		cv2.imshow("Average", cv2.convertScaleAbs(average))

	return (average, last_uploaded, motion_counter)


def security_desktop():
	video_stream = VideoStream(src=0).start()
	print("Warmup")
	time.sleep(config["camera_warmup_time"])
	average = None
	last_uploaded = datetime.datetime.now()
	motion_counter = 0

	while True:
		frame = video_stream.read()
		if frame is None:
			break

		frame = imutils.resize(frame, width=500)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (21, 21), 0)

		if average is None:
			average = gray.copy().astype("float")
			continue

		average, last_uploaded, motion_counter = processing_captures(frame, gray, average, last_uploaded, motion_counter, config)

		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			break

	video_stream.stop()
	cv2.destroyAllWindows()


def security_pi():
	from picamera.array import PiRGBArray
	from picamera import PiCamera

	camera = PiCamera()
	camera.resolution = tuple(config["resolution"])
	camera.framerate = config["fps"]
	rawCapture = PiRGBArray(camera, size=tuple(config["resolution"]))
	average = None

	print("[INFO] warming up...")
	time.sleep(config["camera_warmup_time"])

	last_uploaded = datetime.datetime.now()
	motion_counter = 0

	for raw_frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		frame = raw_frame.array

		frame = imutils.resize(frame, width=500)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (21, 21), 0)

		if average is None:
			print("[INFO] starting background model...")
			average = gray.copy().astype("float")
			rawCapture.truncate(0)
			continue

		average, last_uploaded, motion_counter = processing_captures(frame, gray, average, last_uploaded, motion_counter, config)

		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			break
		rawCapture.truncate(0)



if __name__ == "__main__":
	setup()
	if config["platform"] == 'desktop':
		security_desktop()
	elif config["platform"] == 'pi':
		security_pi()