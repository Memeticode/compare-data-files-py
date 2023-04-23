import streamlit as st
import pandas as pd
from io import BytesIO
from typing import Union
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

def abs_difference_if_numeric(obj1, obj2) -> float:
    if isinstance(obj1, (int, float)) and isinstance(obj2, (int, float)):
        return abs(obj1 - obj2)
    else:
        return None

# Function to get columns that exist in both dataframes
def find_common_columns(df1, df2) -> list[str]:
    if df1 is not None and df2 is not None:
        return list(set(df1.columns) & set(df2.columns))
    return []

# Function to compare dataframe rows
def compare_rows(row1: pd.Series, row2: pd.Series) -> dict:
    differences = {}
    for col in row1.index:
        if row1[col] != row2[col]:
            differences[col] = (row1[col], row2[col])
    return differences

def compare_dataframes_to_diff(df1: pd.DataFrame, df1_name: str, df2: pd.DataFrame, df2_name: str, index_col_names: list[str], compare_col_names: list[str]) -> pd.DataFrame:
    usedf1 = df1.copy()
    usedf1.set_index(index_col_names, inplace=True)
    usedf1.sort_index(inplace=True)
    usedf2 = df2.copy()
    usedf2.set_index(index_col_names, inplace=True)
    usedf2.sort_index(inplace=True)
    diff_data = []
    for idx in usedf1.index.intersection(usedf2.index):
        row1 = usedf1.loc[idx, compare_col_names]
        row2 = usedf2.loc[idx, compare_col_names]
        row_diff = compare_rows(row1, row2)
        
        for col, diff in row_diff.items():
            vdiff = abs_difference_if_numeric(diff[0], diff[1])
            diff_data.append({'data1_name': df1_name,
                              'data2_name': df2_name,
                              'index_col_name': index_col_names,
                              'index_value': idx,
                              'column_name': col,
                              'data1_value': diff[0],
                              'data2_value': diff[1],
                              #'abs_diff': vdiff,
                              })
    diff_df = pd.DataFrame(diff_data)
    return diff_df

def find_rows_in_df1_not_in_df2(df1: pd.DataFrame, df2: pd.DataFrame, index_col_names: list[str]) -> pd.DataFrame:
    usedf1 = df1.copy()
    usedf1.set_index(index_col_names, inplace=True)
    usedf1.sort_index(inplace=True)
    
    usedf2 = df2.copy()
    usedf2.set_index(index_col_names, inplace=True)
    usedf2.sort_index(inplace=True)

    missing_indices = usedf1.index.difference(usedf2.index)
    missing_rows = usedf1.loc[missing_indices]

    return missing_rows.reset_index()


# Return count of unique values in a given df column
def count_unique_values(df: pd.DataFrame, column: str) -> int:
    if column in df.columns:
        return df[column].nunique()
    else:
        raise ValueError(f"The column '{column}' does not exist in the DataFrame.")

def is_not_none_and_dataframe(obj):
    return obj is not None and isinstance(obj, pd.DataFrame)

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
            st.session_state.uploaded_files[i] = file

    # Sheet selection for Excel files with multiple sheets
    for i, file in enumerate(st.session_state.uploaded_files):
        if file is not None and file.type != "text/csv":
            sheet_names = get_excel_sheet_names(file)
            if len(sheet_names) > 1:
                selected_sheet = st.sidebar.selectbox(f"Select Sheet for File {i+1}", sheet_names, key=f"sheet_select_{i}")
                st.session_state.selected_sheets[i] = selected_sheet
            else:
                st.session_state.selected_sheets[i] = None

    # Data comparison configuration
    if st.session_state.uploaded_files[0] is not None and st.session_state.uploaded_files[1] is not None:
        df1 = st.session_state.uploaded_files_data[0]
        df2 = st.session_state.uploaded_files_data[1]
        common_columns = find_common_columns(df1, df2)
        if common_columns:
            st.sidebar.subheader("Data Comparison Configuration")
            if len(st.session_state.shared_id_columns) > 0:
                shared_id_columns = st.sidebar.multiselect("Select Shared Id Column(s)", common_columns, default=st.session_state.shared_id_columns, key="gui_shared_id_columns")
                st.session_state.shared_id_columns = shared_id_columns
            else:
                shared_id_columns = st.sidebar.multiselect("Select Shared Id Column(s)", common_columns, key="gui_shared_id_columns")
                st.session_state.shared_id_columns = shared_id_columns

            # Select "Include In Comparison" columns with a "Select All" option
            include_in_comparison_columns_calc = [col for col in common_columns if not col in st.session_state.shared_id_columns]
            select_all_option = "Select All "
            include_in_comparison_options = [select_all_option] + include_in_comparison_columns_calc
            include_in_comparison_columns = st.sidebar.multiselect("Select Comparison Column(s)", include_in_comparison_options, key="gui_include_in_comparison_columns")

            # If "Select All" is chosen, update the selected columns to include all common columns
            if select_all_option in include_in_comparison_columns:
                include_in_comparison_columns = include_in_comparison_columns_calc

            st.session_state.include_in_comparison_columns = include_in_comparison_columns
        else:
            if st.session_state.uploaded_files[0] == st.session_state.uploaded_files[1] and st.session_state.selected_sheets[0] == st.session_state.selected_sheets[1]:
                st.sidebar.warning("Uploaded file and sheet names are identical.")
            else:
                st.sidebar.warning("No common columns found in the uploaded files.")
            

    # Load data and display the uploaded file names or a message if no files are uploaded
    for i, (file, sheet) in enumerate(zip(st.session_state.uploaded_files, st.session_state.selected_sheets)):
        if file is not None:
            display_text = f"File {i+1}: {file.name}"
            if sheet is not None:
                display_text += f" (Sheet: '{sheet}')"
            df = validate_and_read_file(file, sheet)
            if df is not None:
                st.session_state.uploaded_files[i] = file
                st.session_state.uploaded_files_data[i] = df
            else:
                st.session_state.uploaded_files[i] = None
                st.session_state.uploaded_files_data[i] = df
        else:
            display_text = f"File {i+1}: No file uploaded"

        wrote_info = False
        if st.session_state.uploaded_files_data:
            if len(st.session_state.uploaded_files_data) > i:
                if not st.session_state.uploaded_files_data[i] is None:
                    if any(st.session_state.uploaded_files_data[i]):

                        # If there is data in the table, provide info via expander drop down
                        with st.expander(display_text):
                            file_cols_not_in_comparison = list(st.session_state.uploaded_files_data[i].columns)
                            if st.session_state.shared_id_columns:  
                                for col in st.session_state.shared_id_columns:
                                    if col in file_cols_not_in_comparison:
                                        file_cols_not_in_comparison.remove(col)
                            if st.session_state.include_in_comparison_columns:  
                                for col in st.session_state.include_in_comparison_columns:
                                    if col in file_cols_not_in_comparison:
                                        file_cols_not_in_comparison.remove(col)

                            if any(file_cols_not_in_comparison):
                                st.warning(f"{len(file_cols_not_in_comparison)} columns not in comparison: {', '.join(file_cols_not_in_comparison)}")

                            if st.session_state.shared_id_columns:  
                                duplicates = st.session_state.uploaded_files_data[i].duplicated(subset=st.session_state.shared_id_columns, keep=False)
                                if not duplicates is None:
                                    if any(duplicates):
                                        st.warning(f"{len(duplicates)} duplicates on id column(s): {', '.join(st.session_state.shared_id_columns)}")
                            st.write("Top 5 rows:")
                            st.table(st.session_state.uploaded_files_data[i].head(5))
                            wrote_info = True

        if not wrote_info:
            st.write(display_text)

    # Write compariosn output
    st.subheader("**Comparison**")
    if st.session_state.uploaded_files_data:
        if is_not_none_and_dataframe(st.session_state.uploaded_files_data[0]) and is_not_none_and_dataframe(st.session_state.uploaded_files_data[1]):
            if len(st.session_state.shared_id_columns) > 0 and len(st.session_state.include_in_comparison_columns) > 0:
                file1name = f"{st.session_state.uploaded_files[0].name}{'' if not st.session_state.selected_sheets[0] else '.[' + st.session_state.selected_sheets[0] + ']'}"
                file2name = f"{st.session_state.uploaded_files[1].name}{'' if not st.session_state.selected_sheets[1] else '.[' + st.session_state.selected_sheets[1] + ']'}"
                df1 = st.session_state.uploaded_files_data[0]
                df2 = st.session_state.uploaded_files_data[1]
                idcols = st.session_state.shared_id_columns
                data_in_file1_only = find_rows_in_df1_not_in_df2(df1, df2, idcols)
                if is_not_none_and_dataframe(data_in_file1_only):
                    if any(data_in_file1_only):                        
                        st.write(f"**{len(data_in_file1_only)} row(s) only in {file1name}:**")
                        data_in_file1_only_no_idx = data_in_file1_only.reset_index(drop=True)
                        st.table(data_in_file1_only_no_idx)

                data_in_file2_only = find_rows_in_df1_not_in_df2(df2, df1, idcols)
                if is_not_none_and_dataframe(data_in_file2_only):
                    if any(data_in_file2_only):                        
                        st.write(f"**{len(data_in_file2_only)} row(s) only in {file2name}:**")
                        data_in_file2_only_no_idx = data_in_file2_only.reset_index(drop=True)
                        st.table(data_in_file2_only_no_idx)

                compared_data = compare_dataframes_to_diff(df1, file1name, df2, file2name, idcols, st.session_state.include_in_comparison_columns)
                if is_not_none_and_dataframe(compared_data):
                    if any(compared_data):
                        rows_in_both_with_diff = count_unique_values(compared_data, "index_value")
                        st.write(f"**{rows_in_both_with_diff} row(s) in both with difference:**")
                        compared_data_no_idx = compared_data.reset_index(drop=True)
                        st.table(compared_data_no_idx)



# Initialize session state variables
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = [None, None]
if "uploaded_files_data" not in st.session_state:
    st.session_state.uploaded_files_data = [None, None]
if "selected_sheets" not in st.session_state:
    st.session_state.selected_sheets = [None, None]
if "common_columns" not in st.session_state:
    st.session_state.common_columns = []
if "shared_id_columns" not in st.session_state:
    st.session_state.shared_id_columns = []
if "include_in_comparison_columns" not in st.session_state:
    st.session_state.include_in_comparison_columns = []

if __name__ == "__main__":
    main()

