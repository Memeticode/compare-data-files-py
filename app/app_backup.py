import streamlit as st
import pandas as pd
from io import BytesIO
import base64

# Function to check if the file format is valid (csv or excel)
def validate_and_read_file(file, selected_sheet=None):
    if file is not None:
        file_type = file.type
        if file_type in ["text/csv", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel.sheet.macroenabled.12"]:
            try:
                if file_type == "text/csv":
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file, sheet_name=selected_sheet)
                return df
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return None
    return None

# Function to read sheet names from an Excel file
def get_excel_sheet_names(file):
    if file.type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel.sheet.macroenabled.12"]:
        with pd.ExcelFile(file) as xls:
            return xls.sheet_names
    return []


def main():
    st.set_page_config(page_title="Data Comparison App", layout="wide")
    st.header("Welcome to the Data Comparison App!")
    st.sidebar.title("Upload Files (csv or excel)")

    # Sidebar file uploaders
    file1 = st.sidebar.file_uploader("Upload File 1", type=["csv", "xls", "xlsx", "xlsm"])
    file2 = st.sidebar.file_uploader("Upload File 2", type=["csv", "xls", "xlsx", "xlsm"])

    # Check if the uploaded files have valid formats and store them in session state
    for i, file in enumerate([file1, file2]):
        if file is not None and st.session_state.uploaded_files[i] != file:
            selected_sheet = st.session_state.selected_sheets[i]
            df = validate_and_read_file(file, selected_sheet)
            if df is not None:
                st.session_state.uploaded_files[i] = file
                st.session_state.uploaded_files_data[i] = df
            else:
                st.session_state.uploaded_files[i] = None
                st.session_state.uploaded_files_data[i] = df

    # Sheet selection for Excel files with multiple sheets
    for i, file in enumerate(st.session_state.uploaded_files):
        if file is not None and file.type != "text/csv":
            sheet_names = get_excel_sheet_names(file)
            if len(sheet_names) > 1:
                selected_sheet = st.sidebar.selectbox(f"Select Sheet for File {i+1}", sheet_names, key=f"sheet_select_{i}")
                st.session_state.selected_sheets[i] = selected_sheet
            else:
                st.session_state.selected_sheets[i] = None

    # Display the uploaded file names or a message if no files are uploaded
    for i, (file, sheet) in enumerate(zip(st.session_state.uploaded_files, st.session_state.selected_sheets)):
        if file is not None:
            display_text = f"File {i+1}: {file.name}"
            if sheet is not None:
                display_text += f" (Sheet: '{sheet}')"
        else:
            display_text = f"File {i+1}: No file uploaded"
        st.write(display_text)


# Initialize session state variables
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = [None, None]
if "uploaded_files_data" not in st.session_state:
    st.session_state.uploaded_files_data = [None, None]
if "selected_sheets" not in st.session_state:
    st.session_state.selected_sheets = [None, None]

if __name__ == "__main__":
    main()

