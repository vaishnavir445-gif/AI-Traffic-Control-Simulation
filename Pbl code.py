import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import time

# -----------------------------
# STREAMLIT APP CONFIG
# -----------------------------
st.set_page_config(page_title="AI Traffic Control Simulation", page_icon="🚦", layout="wide")
st.title("🚦 AI Traffic Control Simulation")
st.markdown("### Intelligent Traffic Signal Controller using YOLOv8 + OpenCV")

# -----------------------------
# SIDEBAR SETTINGS
# -----------------------------
st.sidebar.header("⚙️ Settings")
base_time = st.sidebar.slider("Base green signal time (sec)", 5, 20, 10)
extra_time_factor = st.sidebar.slider("Extra time per vehicle (sec)", 1, 5, 2)
num_lanes = st.sidebar.slider("Number of lanes", 2, 4, 3)

source = st.sidebar.radio("Video Source:", ["Upload Video", "Webcam"])
if source == "Upload Video":
    uploaded_file = st.sidebar.file_uploader("Upload traffic video", type=["mp4", "mov", "avi"])
else:
    uploaded_file = None

# -----------------------------
# LOAD YOLO MODEL
# -----------------------------
st.sidebar.info("Loading YOLOv8 model (this may take a few seconds)...")
model = YOLO("yolov8n.pt")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def detect_vehicles(frame, num_lanes):
    """Detects vehicles and counts them per lane."""
    results = model(frame)
    annotated = results[0].plot()
    height, width, _ = frame.shape
    lane_width = width // num_lanes
    lane_counts = [0] * num_lanes

    for box in results[0].boxes.xyxy:
        x1, y1, x2, y2 = box
        cx = int((x1 + x2) / 2)
        lane_index = int(cx // lane_width)
        if 0 <= lane_index < num_lanes:
            lane_counts[lane_index] += 1

    for i in range(1, num_lanes):
        cv2.line(annotated, (i * lane_width, 0), (i * lane_width, height), (0, 255, 255), 2)

    return annotated, lane_counts


def display_lights(lane_counts, base_time, extra_time_factor):
    """Simulate which lane gets green signal based on max density."""
    signal_times = [base_time + extra_time_factor * c for c in lane_counts]
    max_lane = int(np.argmax(lane_counts))

    # UI visualization
    cols = st.columns(len(lane_counts))
    for i, col in enumerate(cols):
        if i == max_lane:
            color = "🟢"
            label = f"**LANE {i+1} — GREEN ({signal_times[i]}s)**"
        else:
            color = "🔴"
            label = f"Lane {i+1} — RED ({signal_times[i]}s)"
        with col:
            st.markdown(f"<div style='text-align:center;font-size:80px'>{color}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center'>{label}</div>", unsafe_allow_html=True)

    return signal_times, max_lane


def show_yellow_phase(max_lane, duration=3):
    """Display yellow transition light for safety."""
    cols = st.columns(num_lanes)
    for i, col in enumerate(cols):
        if i == max_lane:
            color = "🟡"
            label = f"**LANE {i+1} — YELLOW ({duration}s)**"
        else:
            color = "🔴"
            label = f"Lane {i+1} — RED"
        with col:
            st.markdown(f"<div style='text-align:center;font-size:80px'>{color}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:center'>{label}</div>", unsafe_allow_html=True)
    time.sleep(duration)


# -----------------------------
# MAIN APP LOGIC
# -----------------------------
frame_placeholder = st.empty()
st.markdown("---")
info_placeholder = st.empty()

if uploaded_file or source == "Webcam":
    if uploaded_file:
        with open("temp.mp4", "wb") as f:
            f.write(uploaded_file.read())
        cap = cv2.VideoCapture("temp.mp4")
    else:
        cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Detection
        annotated, lane_counts = detect_vehicles(frame, num_lanes)

        # Signal decision
        signal_times, max_lane = display_lights(lane_counts, base_time, extra_time_factor)

        # Show video feed
        frame_placeholder.image(annotated, channels="BGR")

        info_placeholder.markdown(f"""
        ### 🚗 Vehicle Counts per Lane: {lane_counts}  
        **🟢 Active Lane:** Lane {max_lane+1}  
        **Signal Timers (sec):** {signal_times}
        """)

        # 🟡 YELLOW PHASE after GREEN
        show_yellow_phase(max_lane, duration=3)

        time.sleep(0.3)

    cap.release()
else:
    st.warning("⬆️ Upload a traffic video or select webcam to begin simulation.")


