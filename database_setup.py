#!/usr/bin/env python3
"""
Database setup and data parsing for Fantasy Football Draft Analysis
"""

import sqlite3
import pandas as pd
import re
from datetime import datetime
import os

class FantasyFootballDB:
    def __init__(self, db_path="fantasy_draft.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        # Teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT UNIQUE NOT NULL,
                owner_name TEXT
            )
        """)
        
        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                nfl_team TEXT NOT NULL,
                position TEXT NOT NULL,
                UNIQUE(first_name, last_name, nfl_team, position)
            )
        """)
        
        # Drafts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                draft_date DATE,
                league_name TEXT DEFAULT 'La Resistance',
                UNIQUE(year, league_name)
            )
        """)
        
        # Draft picks table (main transaction table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS draft_picks (
                pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                pick_in_round INTEGER NOT NULL,
                overall_pick INTEGER NOT NULL,
                player_status TEXT,
                FOREIGN KEY (draft_id) REFERENCES drafts (draft_id),
                FOREIGN KEY (team_id) REFERENCES teams (team_id),
                FOREIGN KEY (player_id) REFERENCES players (player_id),
                UNIQUE(draft_id, overall_pick)
            )
        """)
        
        self.conn.commit()
        print("✅ Database tables created successfully!")
    
    def parse_player_string(self, player_string):
        """Parse player string to extract components"""
        # Example: "Lamb, CeeDee DAL WR (Q)"
        # Example: "Harrison Jr., Marvin ARI WR (R)"
        # Example: "Williams, Caleb CHI QB (R) (Q)"
        
        # Remove quotes if present
        player_string = player_string.strip('"')
        
        # Extract all status indicators (Q, I, R, etc.) if present
        status_matches = re.findall(r'\(([QIRSP]+)\)', player_string)
        status = ' '.join(status_matches) if status_matches else None
        
        # Remove all status indicators from string
        player_string = re.sub(r'\s*\([QIRSP]+\)', '', player_string)
        
        # Split by last space to separate position
        parts = player_string.rsplit(' ', 1)
        if len(parts) != 2:
            print(f"Warning: Could not parse player string: {player_string}")
            return None
        
        name_and_team = parts[0]
        position = parts[1]
        
        # Split by last space again to separate NFL team
        name_team_parts = name_and_team.rsplit(' ', 1)
        if len(name_team_parts) != 2:
            print(f"Warning: Could not parse name and team: {name_and_team}")
            return None
        
        name_part = name_team_parts[0]
        nfl_team = name_team_parts[1]
        
        # Parse name (handle "Last, First" and "Last Jr., First" formats)
        if ', ' in name_part:
            name_components = name_part.split(', ')
            if len(name_components) == 2:
                last_name = name_components[0]
                first_name = name_components[1]
            else:
                # Handle cases like "Harrison Jr., Marvin"
                last_name = ', '.join(name_components[:-1])
                first_name = name_components[-1]
        else:
            # Fallback for unusual formats
            name_words = name_part.split()
            first_name = name_words[0] if name_words else ""
            last_name = ' '.join(name_words[1:]) if len(name_words) > 1 else ""
        
        return {
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'nfl_team': nfl_team.strip(),
            'position': position.strip(),
            'status': status
        }
    
    def parse_pick_number(self, pick_string):
        """Parse pick number to extract round and pick in round"""
        # Example: "1.01" -> round 1, pick 1
        # Example: "2.10" -> round 2, pick 10
        try:
            round_num, pick_in_round = pick_string.split('.')
            return int(round_num), int(pick_in_round)
        except:
            print(f"Warning: Could not parse pick number: {pick_string}")
            return None, None
    
    def insert_team(self, team_name):
        """Insert team and return team_id"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO teams (team_name) VALUES (?)
        """, (team_name,))
        
        cursor.execute("SELECT team_id FROM teams WHERE team_name = ?", (team_name,))
        return cursor.fetchone()[0]
    
    def insert_player(self, first_name, last_name, nfl_team, position):
        """Insert player and return player_id"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO players (first_name, last_name, nfl_team, position)
            VALUES (?, ?, ?, ?)
        """, (first_name, last_name, nfl_team, position))
        
        cursor.execute("""
            SELECT player_id FROM players 
            WHERE first_name = ? AND last_name = ? AND nfl_team = ? AND position = ?
        """, (first_name, last_name, nfl_team, position))
        return cursor.fetchone()[0]
    
    def insert_draft(self, year, league_name="La Resistance"):
        """Insert draft and return draft_id"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO drafts (year, league_name) VALUES (?, ?)
        """, (year, league_name))
        
        cursor.execute("SELECT draft_id FROM drafts WHERE year = ? AND league_name = ?", 
                      (year, league_name))
        return cursor.fetchone()[0]
    
    def import_csv_data(self, csv_file):
        """Import data from CSV file"""
        print(f"Importing data from {csv_file}...")
        
        df = pd.read_csv(csv_file)
        print(f"Found {len(df)} draft picks to import")
        
        # Assume columns are: year, pick_number, overall_pick, team_name, player_string
        imported_count = 0
        error_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                year = int(row.iloc[0])
                pick_number = str(row.iloc[1])
                overall_pick = int(row.iloc[2])
                team_name = str(row.iloc[3])
                player_string = str(row.iloc[4])
                
                # Skip "No Pick Made" entries
                if player_string.strip().lower() in ['no pick made', 'no pick', 'timer']:
                    skipped_count += 1
                    if skipped_count <= 5:  # Only show first few for brevity
                        print(f"Skipping {player_string} for {team_name} (Pick {overall_pick})")
                    continue
                
                # Parse player info
                player_info = self.parse_player_string(player_string)
                if not player_info:
                    error_count += 1
                    continue
                
                # Parse pick info
                round_num, pick_in_round = self.parse_pick_number(pick_number)
                if not round_num:
                    error_count += 1
                    continue
                
                # Insert/get IDs
                draft_id = self.insert_draft(year)
                team_id = self.insert_team(team_name)
                player_id = self.insert_player(
                    player_info['first_name'],
                    player_info['last_name'],
                    player_info['nfl_team'],
                    player_info['position']
                )
                
                # Insert draft pick
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO draft_picks 
                    (draft_id, team_id, player_id, round_number, pick_in_round, 
                     overall_pick, player_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (draft_id, team_id, player_id, round_num, pick_in_round, 
                      overall_pick, player_info['status']))
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"Imported {imported_count} picks...")
                    
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                error_count += 1
        
        self.conn.commit()
        print(f"✅ Import complete! {imported_count} picks imported, {skipped_count} skipped (no pick made), {error_count} errors")
        return imported_count, error_count

def main():
    """Main function to set up database and import data"""
    # Initialize database
    db = FantasyFootballDB()
    db.connect()
    
    # Create tables
    db.create_tables()
    
    # Import data
    csv_file = "data/2025 Raw La Resistance Data_cleaned.csv"
    if os.path.exists(csv_file):
        db.import_csv_data(csv_file)
    else:
        print(f"❌ CSV file not found: {csv_file}")
    
    # Show some stats
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM draft_picks")
    total_picks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM teams")
    total_teams = cursor.fetchone()[0]
    
    print(f"\n📊 Database Summary:")
    print(f"   - Total draft picks: {total_picks}")
    print(f"   - Unique players: {total_players}")
    print(f"   - Fantasy teams: {total_teams}")
    
    db.close()
    print("🎉 Database setup complete!")

if __name__ == "__main__":
    main()