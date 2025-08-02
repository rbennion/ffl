#!/usr/bin/env python3
"""
Check for non-standard characters in CSV file
"""

import csv
import re
import unicodedata
from collections import defaultdict

def find_nonstandard_characters(file_path):
    """Find and report non-standard characters in CSV file"""
    
    # Track different types of characters
    nonstandard_chars = defaultdict(list)
    special_chars = defaultdict(list)
    unicode_chars = defaultdict(list)
    
    # Standard ASCII printable characters (32-126)
    standard_ascii = set(chr(i) for i in range(32, 127))
    
    line_num = 0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line_num += 1
            
            for pos, char in enumerate(line):
                # Check for non-standard characters
                if char not in standard_ascii:
                    char_info = {
                        'char': char,
                        'unicode_name': unicodedata.name(char, 'UNKNOWN'),
                        'unicode_code': f'U+{ord(char):04X}',
                        'line': line_num,
                        'position': pos,
                        'context': line[max(0, pos-10):pos+10].strip()
                    }
                    
                    if ord(char) > 127:
                        unicode_chars[char].append(char_info)
                    else:
                        nonstandard_chars[char].append(char_info)
                
                # Also check for specific problematic characters
                if char in ['\xa0', '\u2009', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u200a', '\u200b']:
                    special_chars[char].append(char_info)
    
    # Report findings
    print("=== NON-STANDARD CHARACTER ANALYSIS ===\n")
    
    if nonstandard_chars:
        print("NON-ASCII CHARACTERS FOUND:")
        print("-" * 40)
        for char, occurrences in nonstandard_chars.items():
            print(f"Character: '{char}' (U+{ord(char):04X}) - {unicodedata.name(char, 'UNKNOWN')}")
            print(f"  Occurrences: {len(occurrences)}")
            print(f"  First occurrence: Line {occurrences[0]['line']}, Position {occurrences[0]['position']}")
            print(f"  Context: ...{occurrences[0]['context']}...")
            print()
    
    if unicode_chars:
        print("UNICODE CHARACTERS FOUND:")
        print("-" * 40)
        for char, occurrences in unicode_chars.items():
            print(f"Character: '{char}' (U+{ord(char):04X}) - {unicodedata.name(char, 'UNKNOWN')}")
            print(f"  Occurrences: {len(occurrences)}")
            print(f"  First occurrence: Line {occurrences[0]['line']}, Position {occurrences[0]['position']}")
            print(f"  Context: ...{occurrences[0]['context']}...")
            print()
    
    if special_chars:
        print("SPECIAL WHITESPACE/INVISIBLE CHARACTERS:")
        print("-" * 40)
        for char, occurrences in special_chars.items():
            print(f"Character: '{repr(char)}' (U+{ord(char):04X}) - {unicodedata.name(char, 'UNKNOWN')}")
            print(f"  Occurrences: {len(occurrences)}")
            print(f"  First occurrence: Line {occurrences[0]['line']}, Position {occurrences[0]['position']}")
            print()
    
    if not nonstandard_chars and not unicode_chars and not special_chars:
        print("✅ No non-standard characters found!")
    
    # Summary
    total_nonstandard = sum(len(occurrences) for occurrences in nonstandard_chars.values())
    total_unicode = sum(len(occurrences) for occurrences in unicode_chars.values())
    total_special = sum(len(occurrences) for occurrences in special_chars.values())
    
    print(f"\nSUMMARY:")
    print(f"- Non-ASCII characters: {total_nonstandard}")
    print(f"- Unicode characters: {total_unicode}")
    print(f"- Special whitespace: {total_special}")
    print(f"- Total lines processed: {line_num}")

if __name__ == "__main__":
    csv_file = "data/2025 Raw La Resistance Data.csv"
    find_nonstandard_characters(csv_file)