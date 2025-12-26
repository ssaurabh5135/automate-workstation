import streamlit as st
import pandas as pd
from datetime import datetime
import os
from pyzbar.pyzbar import decode
from PIL import Image, ImageEnhance

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
    """Decode barcode using pure pyzbar (NO OpenCV)"""
    try:
        # Enhance image for better barcode detection
        enhancer = ImageEnhance.Contrast(image)
        image_enhanced = enhancer.enhance(2.0)
        
        # Decode barcodes directly from PIL image
        barcodes = decode(image_enhanced)
        
        if barcodes:
            barcode_data = barcodes[0].data.decode('utf-8').strip()
            return barcode_data
        return None
    except Exception as e:
        st.error(f"Decode error: {str(e)}")
        return None

def save_to_excel(data):
    df_new = pd.DataFrame([data])
    if os.path.exists(EXCEL_FILE):
        df_old = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_excel(EXCEL_FILE, index=False)

def reset_system():
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
    
    image = st.camera_input("Point camera at barcode and capture")
    
    if image:
        st.session_state.scanned_image = image
        
        with st.spinner("🔍 Scanning barcode..."):
            scanned_part_no = decode_barcode(image)
        
        if scanned_part_no:
            st.session_state.part_no = scanned_part_no
            
            try:
                defect_master = pd.read_csv(DEFECT_FILE)
                matching_defects = defect_master[
                    defect_master["part_no"].astype(str) == scanned_part_no
                ].to_dict("records")
                
                if len(matching_defects) == 0:
                    st.warning(f"No defects found for: {scanned_part_no}")
                    st.session_state.defects = [{"defect_code": "GENERAL", "defect_name": f"Part {scanned_part_no}"}]
                else:
                    st.session_state.defects = matching_defects
                    st.success(f"✅ Scanned: **{scanned_part_no}** ({len(st.session_state.defects)} defects)")
                    
            except FileNotFoundError:
                st.error("❌ defects_master.csv missing!")
                st.session_state.defects = [{"defect_code": "GENERAL", "defect_name": scanned_part_no}]
            
            st.rerun()
        else:
            st.error("❌ No barcode found! Try better lighting/angle.")
            st.image(image, caption="No barcode detected", use_column_width=True)

# =========================================================
# STEP 2 : DEFECT CHECKSHEET
# =========================================================
else:
    part_no = st.session_state.part_no
    defects = st.session_state.defects
    idx = st.session_state.current_index

    if st.session_state.scanned_image:
        st.image(st.session_state.scanned_image, caption=f"Part: {part_no}", use_column_width=True)

    st.info(f"🔧 Part: **{part_no}**")

    if idx < len(defects):
        defect = defects[idx]
        st.markdown(f"### {idx + 1}/{len(defects)} - **{defect['defect_name']}**")
        st.caption(f"Code: {defect.get('defect_code', 'N/A')}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ OK", use_container_width=True):
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
        st.success("🎉 Inspection Complete!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Next Part"):
                reset_system()
                st.rerun()
        with col2:
            if st.button("🗑️ Clear All"):
                reset_system()
                if os.path.exists(EXCEL_FILE):
                    os.remove(EXCEL_FILE)
                st.rerun()

# =========================================================
# DATA VIEW
# =========================================================
st.divider()
st.subheader("📊 Inspection Records")

if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.metric("Total Records", len(df))
else:
    st.info("No data yet")



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
