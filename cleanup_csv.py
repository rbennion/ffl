#!/usr/bin/env python3
"""
Clean up non-standard characters in CSV file
"""

import csv
import re
import unicodedata
import os
from datetime import datetime

def clean_csv_file(input_file, output_file=None, backup=True):
    """Clean non-standard characters from CSV file"""
    
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_cleaned.csv"
    
    # Create backup if requested
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{os.path.splitext(input_file)[0]}_backup_{timestamp}.csv"
        print(f"Creating backup: {backup_file}")
        with open(input_file, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    # Track changes
    changes_made = {
        'non_breaking_spaces': 0,
        'other_unicode': 0,
        'lines_processed': 0
    }
    
    print(f"Cleaning file: {input_file}")
    print(f"Output file: {output_file}")
    print()
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        for row_num, row in enumerate(reader, 1):
            cleaned_row = []
            
            for cell in row:
                original_cell = cell
                
                # Replace non-breaking spaces with regular spaces
                cleaned_cell = cell.replace('\xa0', ' ')
                if cleaned_cell != cell:
                    changes_made['non_breaking_spaces'] += cell.count('\xa0')
                
                # Replace other problematic Unicode whitespace characters
                unicode_whitespace = [
                    '\u2009',  # THIN SPACE
                    '\u2002',  # EN SPACE
                    '\u2003',  # EM SPACE
                    '\u2004',  # THREE-PER-EM SPACE
                    '\u2005',  # FOUR-PER-EM SPACE
                    '\u2006',  # SIX-PER-EM SPACE
                    '\u2007',  # FIGURE SPACE
                    '\u2008',  # PUNCTUATION SPACE
                    '\u200a',  # HAIR SPACE
                    '\u200b',  # ZERO WIDTH SPACE
                ]
                
                for unicode_char in unicode_whitespace:
                    if unicode_char in cleaned_cell:
                        changes_made['other_unicode'] += cleaned_cell.count(unicode_char)
                        cleaned_cell = cleaned_cell.replace(unicode_char, ' ')
                
                # Clean up multiple consecutive spaces
                cleaned_cell = re.sub(r' +', ' ', cleaned_cell)
                
                # Strip leading/trailing whitespace
                cleaned_cell = cleaned_cell.strip()
                
                cleaned_row.append(cleaned_cell)
            
            writer.writerow(cleaned_row)
            changes_made['lines_processed'] += 1
            
            # Show progress every 100 lines
            if row_num % 100 == 0:
                print(f"Processed {row_num} lines...")
    
    # Report results
    print(f"\n✅ Cleaning completed!")
    print(f"📊 SUMMARY:")
    print(f"   - Lines processed: {changes_made['lines_processed']}")
    print(f"   - Non-breaking spaces fixed: {changes_made['non_breaking_spaces']}")
    print(f"   - Other Unicode characters fixed: {changes_made['other_unicode']}")
    print(f"   - Output saved to: {output_file}")
    
    if backup:
        print(f"   - Backup saved to: {backup_file}")
    
    return output_file, changes_made

def verify_cleaning(original_file, cleaned_file):
    """Verify that cleaning was successful"""
    print(f"\n🔍 VERIFICATION:")
    
    # Count non-standard characters in both files
    def count_nonstandard(file_path):
        nonstandard_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            nonstandard_count = content.count('\xa0')
            for unicode_char in ['\u2009', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u200a', '\u200b']:
                nonstandard_count += content.count(unicode_char)
        return nonstandard_count
    
    original_count = count_nonstandard(original_file)
    cleaned_count = count_nonstandard(cleaned_file)
    
    print(f"   - Original file non-standard chars: {original_count}")
    print(f"   - Cleaned file non-standard chars: {cleaned_count}")
    
    if cleaned_count == 0:
        print("   ✅ All non-standard characters successfully removed!")
    else:
        print(f"   ⚠️  {cleaned_count} non-standard characters remain")
    
    return cleaned_count == 0

if __name__ == "__main__":
    input_csv = "data/2025 Raw La Resistance Data.csv"
    
    if os.path.exists(input_csv):
        # Clean the file
        output_file, changes = clean_csv_file(input_csv)
        
        # Verify the results
        verify_cleaning(input_csv, output_file)
        
        print(f"\n🎯 Your cleaned fantasy football data is ready!")
        print(f"   Use: {output_file}")
        
    else:
        print(f"❌ File not found: {input_csv}")