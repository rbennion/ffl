#!/usr/bin/env python3
"""
Convert Excel file to CSV format
"""

import pandas as pd
import sys
import os

def convert_excel_to_csv(excel_file_path, output_csv_path=None):
    """Convert Excel file to CSV"""
    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_file_path}")
        
        # First, let's see what sheets are available
        excel_file = pd.ExcelFile(excel_file_path)
        print(f"Available sheets: {excel_file.sheet_names}")
        
        # If no output path specified, create one based on input filename
        if output_csv_path is None:
            base_name = os.path.splitext(excel_file_path)[0]
            output_csv_path = f"{base_name}.csv"
        
        # Read the first sheet (or specify sheet name if needed)
        df = pd.read_excel(excel_file_path, sheet_name=0)
        
        print(f"Excel file shape: {df.shape} (rows, columns)")
        print(f"Column names: {list(df.columns)}")
        
        # Save to CSV
        df.to_csv(output_csv_path, index=False)
        print(f"Successfully converted to CSV: {output_csv_path}")
        
        # Show first few rows
        print("\nFirst 5 rows of data:")
        print(df.head())
        
        return True
        
    except Exception as e:
        print(f"Error converting file: {e}")
        return False

if __name__ == "__main__":
    excel_file = "data/2025 Raw La Resistance Data.xlsx"
    
    if os.path.exists(excel_file):
        convert_excel_to_csv(excel_file)
    else:
        print(f"File not found: {excel_file}")