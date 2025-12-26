import streamlit as st
import pandas as pd
from datetime import datetime
import os
import cv2
import numpy as np
from pyzbar import pyzbar
from PIL import Image

# ---------------- CONFIG ----------------
DATA_DIR = "data"
EXCEL_FILE = f"{DATA_DIR}/inspection.xlsx"
DEFECT_FILE = "defects_master.csv"

os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(
    page_title="Inspection System Prototype",
    layout="centered"
)

# ---------------- SESSION STATE ----------------
if "part_no" not in st.session_state:
    st.session_state.part_no = None
if "defects" not in st.session_state:
    st.session_state.defects = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "scanned_image" not in st.session_state:
    st.session_state.scanned_image = None

# ---------------- FUNCTIONS ----------------
def decode_barcode(image):
    """Decode barcode from image using pyzbar"""
    try:
        # Convert PIL to OpenCV format
        opencv_image = np.array(image)
        opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)
        
        # Decode barcodes
        barcodes = pyzbar.decode(opencv_image)
        
        if barcodes:
            # Get first barcode data
            barcode_data = barcodes[0].data.decode('utf-8')
            return barcode_data.strip()
        return None
    except Exception as e:
        st.error(f"Barcode decode error: {str(e)}")
        return None

def save_to_excel(data):
    """Save inspection data to Excel"""
    df_new = pd.DataFrame([data])
    if os.path.exists(EXCEL_FILE):
        df_old = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_excel(EXCEL_FILE, index=False)
    st.success("✅ Data saved successfully!")

def reset_system():
    """Reset all session state"""
    st.session_state.part_no = None
    st.session_state.defects = []
    st.session_state.current_index = 0
    st.session_state.scanned_image = None

# ---------------- UI ----------------
st.title("🔍 Quality Inspection Checksheet")

# =========================================================
# STEP 1 : SCAN BARCODE
# =========================================================
if st.session_state.part_no is None:
    st.subheader("📷 Scan Part Barcode")
    
    # Camera input for actual barcode scanning
    image = st.camera_input("Point camera at barcode and capture")
    
    if image:
        st.session_state.scanned_image = image
        
        # Decode actual barcode
        with st.spinner("🔍 Decoding barcode..."):
            scanned_part_no = decode_barcode(image)
        
        if scanned_part_no:
            st.session_state.part_no = scanned_part_no
            
            # Load defects for this part
            try:
                defect_master = pd.read_csv(DEFECT_FILE)
                st.session_state.defects = defect_master[
                    defect_master["part_no"].astype(str) == scanned_part_no
                ].to_dict("records")
                
                if len(st.session_state.defects) == 0:
                    st.warning(f"No defects found for Part No: {scanned_part_no}")
                    st.info("Continuing with inspection anyway...")
                    # Create empty defects list to proceed
                    st.session_state.defects = [{"defect_code": "GENERAL", "defect_name": "General Inspection"}]
                else:
                    st.success(f"✅ Part No Scanned: **{scanned_part_no}**")
                    st.success(f"Found {len(st.session_state.defects)} defects to inspect")
                    
            except FileNotFoundError:
                st.error("❌ defects_master.csv not found!")
                st.session_state.defects = [{"defect_code": "GENERAL", "defect_name": f"Part {scanned_part_no}"}]
            
            st.rerun()
        else:
            st.error("❌ No barcode detected! Try again with better lighting/angle.")
            st.image(image, caption="Captured image (no barcode found)", use_column_width=True)

# =========================================================
# STEP 2 : DEFECT CHECKSHEET
# =========================================================
else:
    part_no = st.session_state.part_no
    defects = st.session_state.defects
    idx = st.session_state.current_index

    # Show scanned image
    if st.session_state.scanned_image:
        st.image(st.session_state.scanned_image, caption=f"Scanned Part: {part_no}", use_column_width=True)

    st.info(f"🔧 Inspecting Part: **{part_no}**")

    if idx < len(defects):
        defect = defects[idx]
        st.markdown(
            f"""
            ### Defect {idx + 1} of {len(defects)}
            **{defect['defect_name']}**  
            *Code: {defect.get('defect_code', 'N/A')}*
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ OK", use_container_width=True, type="primary"):
                save_to_excel({
                    "Part No": part_no,
                    "Defect Code": defect.get("defect_code", "N/A"),
                    "Defect Name": defect["defect_name"],
                    "Result": "OK",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.current_index += 1
                st.rerun()

        with col2:
            if st.button("❌ NOT OK", use_container_width=True):
                save_to_excel({
                    "Part No": part_no,
                    "Defect Code": defect.get("defect_code", "N/A"),
                    "Defect Name": defect["defect_name"],
                    "Result": "NOT OK",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.current_index += 1
                st.rerun()

    else:
        st.success("🎉 **Inspection Completed Successfully!**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Scan Next Part", use_container_width=True, type="primary"):
                reset_system()
                st.rerun()
        with col2:
            if st.button("🗑️ Clear All Data", use_container_width=True):
                reset_system()
                if os.path.exists(EXCEL_FILE):
                    os.remove(EXCEL_FILE)
                st.success("All data cleared!")
                st.rerun()

# =========================================================
# VIEW SAVED DATA
# =========================================================
st.divider()
st.subheader("📊 Saved Inspection Data")

if os.path.exists(EXCEL_FILE):
    try:
        df_view = pd.read_excel(EXCEL_FILE)
        st.dataframe(df_view, use_container_width=True, hide_index=True)
        st.metric("Total Inspections", len(df_view))
    except Exception as e:
        st.error(f"Error reading data: {str(e)}")
else:
    st.info("No inspection data saved yet")

# Footer
st.markdown("---")
st.caption("💡 Tips: Ensure good lighting, hold steady, and position barcode clearly in frame")


################################################

# import streamlit as st
# import pandas as pd
# from datetime import datetime
# import os

# # ---------------- CONFIG ----------------
# DATA_DIR = "data"
# EXCEL_FILE = f"{DATA_DIR}/inspection.xlsx"
# DEFECT_FILE = "defects_master.csv"

# os.makedirs(DATA_DIR, exist_ok=True)

# st.set_page_config(
#     page_title="Inspection System Prototype",
#     layout="centered"
# )

# # ---------------- SESSION STATE ----------------
# if "part_no" not in st.session_state:
#     st.session_state.part_no = None
# if "defects" not in st.session_state:
#     st.session_state.defects = []
# if "current_index" not in st.session_state:
#     st.session_state.current_index = 0

# # ---------------- FUNCTIONS ----------------
# def save_to_excel(data):
#     df_new = pd.DataFrame([data])
#     if os.path.exists(EXCEL_FILE):
#         df_old = pd.read_excel(EXCEL_FILE)
#         df = pd.concat([df_old, df_new], ignore_index=True)
#     else:
#         df = df_new
#     df.to_excel(EXCEL_FILE, index=False)

# def reset_system():
#     st.session_state.part_no = None
#     st.session_state.defects = []
#     st.session_state.current_index = 0

# # ---------------- UI ----------------
# st.title("🔍 Quality Inspection Checksheet")

# # =========================================================
# # STEP 1 : SCAN BARCODE
# # =========================================================
# if st.session_state.part_no is None:
#     st.subheader("Scan Part Barcode")
    
#     # Camera input for barcode scanning
#     image = st.camera_input("Open camera and scan barcode")
    
#     if image:
#         # Simulate barcode decoding
#         scanned_part_no = "1001"  # Replace with real barcode decode logic
        
#         st.session_state.part_no = scanned_part_no
        
#         defect_master = pd.read_csv(DEFECT_FILE)
#         st.session_state.defects = defect_master[
#             defect_master["part_no"] == int(scanned_part_no)
#         ].to_dict("records")

#         if len(st.session_state.defects) == 0:
#             st.error("No defects mapped for this part!")
#             reset_system()
#         else:
#             st.success(f"Part No Scanned: {scanned_part_no}")
#             st.rerun()

# # =========================================================
# # STEP 2 : DEFECT CHECKSHEET
# # =========================================================
# else:
#     part_no = st.session_state.part_no
#     defects = st.session_state.defects
#     idx = st.session_state.current_index

#     st.info(f"Part Number : {part_no}")

#     if idx < len(defects):
#         defect = defects[idx]
#         st.markdown(
#             f"""
#             ### Defect {idx + 1} of {len(defects)}
#             **{defect['defect_name']}**
#             """
#         )

#         col1, col2 = st.columns(2)
#         with col1:
#             if st.button("✅ OK", use_container_width=True):
#                 save_to_excel({
#                     "Part No": part_no,
#                     "Defect Code": defect["defect_code"],
#                     "Defect Name": defect["defect_name"],
#                     "Result": "OK",
#                     "Timestamp": datetime.now()
#                 })
#                 st.session_state.current_index += 1
#                 st.rerun()

#         with col2:
#             if st.button("❌ NOT OK", use_container_width=True):
#                 save_to_excel({
#                     "Part No": part_no,
#                     "Defect Code": defect["defect_code"],
#                     "Defect Name": defect["defect_name"],
#                     "Result": "NOT OK",
#                     "Timestamp": datetime.now()
#                 })
#                 st.session_state.current_index += 1
#                 st.rerun()
#     else:
#         st.success("✔ Inspection Completed")

#         if st.button("Scan Next Part"):
#             reset_system()
#             st.rerun()

#         # Clear button for manual reset
#         if st.button("Clear Data"):
#             reset_system()
#             if os.path.exists(EXCEL_FILE):
#                 os.remove(EXCEL_FILE)
#             st.rerun()

# # =========================================================
# # VIEW EXCEL DATA (OPTIONAL)
# # =========================================================
# st.divider()
# st.subheader("📊 Inspection Data")

# if os.path.exists(EXCEL_FILE):
#     df_view = pd.read_excel(EXCEL_FILE)
#     st.dataframe(df_view, use_container_width=True)
# else:
#     st.write("No inspection data available")
