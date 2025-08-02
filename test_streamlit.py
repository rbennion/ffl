#!/usr/bin/env python3
"""
Simple test version of the Fantasy Football app
"""

import streamlit as st
import pandas as pd
import sqlite3

# Page config
st.set_page_config(
    page_title="Fantasy Football Test",
    page_icon="🏈",
    layout="wide"
)

st.title("🏈 Fantasy Football Draft Analysis - Test")

# Test database connection
try:
    conn = sqlite3.connect("fantasy_draft.db")
    
    # Simple query
    query = """
    SELECT 
        dp.overall_pick,
        dp.round_number,
        t.team_name,
        p.first_name,
        p.last_name,
        p.position
    FROM draft_picks dp
    JOIN teams t ON dp.team_id = t.team_id
    JOIN players p ON dp.player_id = p.player_id
    ORDER BY dp.overall_pick
    LIMIT 50
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        st.success(f"✅ Database connected! Found {len(df)} draft picks (showing first 50)")
        
        # Simple metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Picks Shown", len(df))
        with col2:
            st.metric("Unique Teams", df['team_name'].nunique())
        with col3:
            st.metric("Unique Positions", df['position'].nunique())
        
        # Simple data table
        st.subheader("Recent Draft Picks")
        st.dataframe(df.head(20), use_container_width=True)
        
        # Simple bar chart using st.bar_chart
        st.subheader("Position Distribution")
        position_counts = df['position'].value_counts()
        st.bar_chart(position_counts)
        
    else:
        st.error("Database connected but no data found")
        
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.info("Make sure you've run database_setup.py first!")