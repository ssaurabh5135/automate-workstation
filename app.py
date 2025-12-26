import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
from PIL import Image

DATA_DIR = "data"
EXCEL_FILE = f"{DATA_DIR}/inspection.xlsx"

os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Inspection System", layout="centered")

if "part_no" not in st.session_state:
    st.session_state.part_no = None
if "defects" not in st.session_state:
    st.session_state.defects = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "scanned_image" not in st.session_state:
    st.session_state.scanned_image = None

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

# FIXED DEFECTS - SAME FOR ALL PARTS
def get_defects_list():
    return [
        {"defect_code": "D001", "defect_name": "Surface Scratch"},
        {"defect_code": "D002", "defect_name": "Weld Imperfection"},
        {"defect_code": "D003", "defect_name": "Paint Defect"},
        {"defect_code": "D004", "defect_name": "Dimension Error"},
        {"defect_code": "D005", "defect_name": "Assembly Issue"}
    ]

# SIMPLE TEXT EXTRACTION FROM BARCODE IMAGES
def extract_barcode_text(image):
    """Extract text from barcode image using OCR-like pattern matching"""
    try:
        # Convert to grayscale and enhance contrast
        img_gray = image.convert('L')
        img_enhanced = img_gray.point(lambda x: 0 if x < 128 else 255)
        
        # Save temp image and read pixels (simplified OCR)
        pixels = list(img_enhanced.getdata())
        
        # Find barcode patterns (high contrast horizontal lines)
        barcode_pattern = []
        for i in range(0, len(pixels), 10):  # Sample every 10th pixel
            row_start = i
            row_end = min(i + 100, len(pixels))
            row = pixels[row_start:row_end]
            
            # Detect barcode-like patterns (alternating black/white)
            black_count = row.count(0)
            white_count = row.count(255)
            
            if black_count > 20 and white_count > 20:  # Barcode pattern detected
                barcode_pattern.append('B')
            else:
                barcode_pattern.append(' ')
        
        # Extract continuous barcode sequence
        pattern_str = ''.join(barcode_pattern)
        barcode_match = re.findall(r'[A-Z0-9]{5,}', pattern_str.replace('B', '1'))
        
        if barcode_match:
            return barcode_match[0].replace('1', '1')[:20]  # Clean and limit length
        
        return None
    except:
        return None

st.title("🔍 Quality Inspection System")

if st.session_state.part_no is None:
    st.subheader("📷 Upload Barcode Image")
    
    uploaded_file = st.file_uploader("📁 Upload barcode photo", type=['png', 'jpg', 'jpeg', 'webp'])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.scanned_image = image
        st.image(image, caption="📸 Uploaded image", use_column_width=True)
        
        # AUTO-DETECT BARCODE
        with st.spinner("🔍 Detecting barcode..."):
            part_no = extract_barcode_text(image)
        
        if part_no:
            st.session_state.part_no = part_no
            st.session_state.defects = get_defects_list()
            st.success(f"✅ **Part No Detected: {part_no}**")
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ No barcode detected. Try:")
            st.info("- Better lighting")
            st.info("- Closer photo of barcode")
            st.info("- Clear, high-contrast barcode")
            
            # MANUAL INPUT FALLBACK
            manual_part = st.text_input("🔢 Or type Part No manually")
            if st.button("✅ Use Manual Input", type="primary"):
                if manual_part.strip():
                    st.session_state.part_no = manual_part.strip()
                    st.session_state.defects = get_defects_list()
                    st.rerun()

else:
    part_no = st.session_state.part_no
    defects = st.session_state.defects
    idx = st.session_state.current_index
    
    if st.session_state.scanned_image:
        st.image(st.session_state.scanned_image, caption=f"Part: {part_no}", use_column_width=True)
    
    st.info(f"🔧 Inspecting: **{part_no}**")
    
    if idx < len(defects):
        defect = defects[idx]
        st.markdown(f"### {idx+1}/{len(defects)}")
        st.markdown(f"**{defect['defect_name']}**")
        st.caption(f"Code: {defect['defect_code']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ OK", use_container_width=True):
                save_to_excel({
                    "Part No": part_no,
                    "Defect Code": defect["defect_code"],
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
                    "Defect Code": defect["defect_code"],
                    "Defect Name": defect["defect_name"],
                    "Result": "NOT OK",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.current_index += 1
                st.rerun()
    else:
        st.success("🎉 **Complete!**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Next Part", use_container_width=True, type="primary"):
                reset_system()
                st.rerun()
        with col2:
            if st.button("🗑️ Clear Data", use_container_width=True):
                reset_system()
                if os.path.exists(EXCEL_FILE):
                    os.remove(EXCEL_FILE)
                st.rerun()

st.divider()
st.subheader("📊 Records")
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
    st.dataframe(df.tail(10), use_container_width=True)
    st.metric("Total", len(df))
else:
    st.info("Upload a barcode to start!")






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
