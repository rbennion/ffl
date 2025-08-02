#!/usr/bin/env python3
"""
Fantasy Football Draft Analysis - Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from database_setup import FantasyFootballDB

# Page config
st.set_page_config(
    page_title="La Resistance Draft Analysis",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_database():
    db = FantasyFootballDB()
    db.connect()
    return db

# Data loading functions
@st.cache_data
def load_draft_data():
    """Load all draft data"""
    db = get_database()
    query = """
    SELECT 
        dp.overall_pick,
        dp.round_number,
        dp.pick_in_round,
        d.year,
        t.team_name,
        p.first_name,
        p.last_name,
        p.nfl_team,
        p.position,
        dp.player_status
    FROM draft_picks dp
    JOIN drafts d ON dp.draft_id = d.draft_id
    JOIN teams t ON dp.team_id = t.team_id
    JOIN players p ON dp.player_id = p.player_id
    ORDER BY d.year, dp.overall_pick
    """
    return pd.read_sql_query(query, db.conn)

@st.cache_data
def load_position_analysis():
    """Load position-based analysis data"""
    db = get_database()
    query = """
    SELECT 
        p.position,
        dp.round_number,
        COUNT(*) as picks_count,
        AVG(dp.overall_pick) as avg_pick,
        MIN(dp.overall_pick) as earliest_pick,
        MAX(dp.overall_pick) as latest_pick
    FROM draft_picks dp
    JOIN players p ON dp.player_id = p.player_id
    GROUP BY p.position, dp.round_number
    ORDER BY dp.round_number, picks_count DESC
    """
    return pd.read_sql_query(query, db.conn)

@st.cache_data
def load_team_analysis():
    """Load team drafting patterns"""
    db = get_database()
    query = """
    SELECT 
        t.team_name,
        p.position,
        dp.round_number,
        COUNT(*) as picks_count,
        AVG(dp.overall_pick) as avg_pick
    FROM draft_picks dp
    JOIN teams t ON dp.team_id = t.team_id
    JOIN players p ON dp.player_id = p.player_id
    GROUP BY t.team_name, p.position, dp.round_number
    ORDER BY t.team_name, dp.round_number
    """
    return pd.read_sql_query(query, db.conn)

# Main app
def main():
    # Title and header
    st.title("🏈 La Resistance Fantasy Football Draft Analysis")
    st.markdown("### Analyze draft patterns, strategies, and trends")
    
    # Load data
    df = load_draft_data()
    
    if df.empty:
        st.error("No draft data found! Please run database_setup.py first.")
        return
    
    # Filters in main area (much more visible!)
    st.markdown("---")
    st.markdown("### 📊 FILTERS")
    
    # Create filter columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Year filter
        years = sorted(df['year'].unique(), reverse=True)
        selected_years = st.multiselect("📅 Select Years", years, default=[], placeholder="Filter Years")
    
    with col2:
        # Position filter
        positions = sorted(df['position'].unique())
        selected_positions = st.multiselect("🏈 Select Positions", positions, default=[], placeholder="Filter Positions")
    
    with col3:
        # Team filter
        teams = sorted(df['team_name'].unique())
        selected_teams = st.multiselect("👥 Select Teams", teams, default=[], placeholder="Filter Teams")
    
    # Filter data - if nothing selected, show all data
    filtered_df = df.copy()
    
    if selected_years:
        filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]
    
    if selected_positions:
        filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]
    
    if selected_teams:
        filtered_df = filtered_df[filtered_df['team_name'].isin(selected_teams)]
    
    # Show filter status right below filters
    if not selected_years and not selected_positions and not selected_teams:
        st.success("📊 **Showing all data** - Select filters above to narrow your analysis")
    else:
        filters_applied = []
        if selected_years: 
            if len(selected_years) == len(years):
                filters_applied.append("All Years")
            else:
                filters_applied.append(f"{len(selected_years)} Year(s)")
        if selected_positions:
            if len(selected_positions) == len(positions):
                filters_applied.append("All Positions")
            else:
                filters_applied.append(f"{len(selected_positions)} Position(s)")
        if selected_teams:
            if len(selected_teams) == len(teams):
                filters_applied.append("All Teams")
            else:
                filters_applied.append(f"{len(selected_teams)} Team(s)")
        st.info(f"🔍 **Filtered by: {', '.join(filters_applied)}** • Clear selections above to see all data")
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Position Analysis", "📊 Round Analysis", "🔢 Pick Analysis", "👥 Team Analysis", "🔍 Player Lookup"])
    
    with tab1:
        position_analysis_tab(filtered_df)
    
    with tab2:
        round_analysis_tab(filtered_df)
    
    with tab3:
        pick_analysis_tab(filtered_df)
    
    with tab4:
        team_analysis_tab(filtered_df)
    
    with tab5:
        player_lookup_tab(df)



def position_analysis_tab(df):
    """Position analysis tab"""
    st.header("🎯 Position Analysis")
    
    # Quick stats at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Picks", len(df))
    
    with col2:
        st.metric("Unique Players", df['first_name'].nunique())
    
    with col3:
        st.metric("Positions", df['position'].nunique())
    
    with col4:
        st.metric("Years Covered", len(df['year'].unique()))
    
    # Position by round heatmap
    st.subheader("Position Selection by Round")
    
    position_round = df.groupby(['round_number', 'position']).size().reset_index(name='count')
    pivot_data = position_round.pivot(index='position', columns='round_number', values='count').fillna(0)
    
    fig_heatmap = px.imshow(
        pivot_data.values,
        x=[f"Round {i}" for i in pivot_data.columns],
        y=pivot_data.index,
        title="Position Selection Heatmap",
        color_continuous_scale="Viridis",
        text_auto=True,  # Add numbers to each cell
        aspect="auto"    # Better spacing
    )
    
    # Improve layout and readability
    fig_heatmap.update_layout(
        font=dict(size=11),
        title_font_size=16,
        xaxis_title="Draft Round",
        yaxis_title="Position",
        coloraxis_colorbar=dict(
            title="Number of Picks",
            title_font_size=12
        )
    )
    
    # Make text more readable
    fig_heatmap.update_traces(
        textfont_size=11,
        textfont_color="white"  # White text for better contrast
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Average draft position by position
    st.subheader("Average Draft Position (ADP) by Position")
    
    adp_data = df.groupby('position')['overall_pick'].agg(['mean', 'std', 'min', 'max']).round(1)
    adp_data = adp_data.sort_values('mean')
    
    adp_df = pd.DataFrame({
        'Position': adp_data.index,
        'Average_Pick': adp_data['mean'],
        'Std_Dev': adp_data['std']
    })
    
    fig_adp = px.bar(
        adp_df,
        x='Position',
        y='Average_Pick',
        error_y='Std_Dev',
        title="Average Draft Position by Position",
        labels={'Position': 'Position', 'Average_Pick': 'Average Pick Number'}
    )
    st.plotly_chart(fig_adp, use_container_width=True)
    
    # Position scarcity analysis - All positions with filtering
    st.subheader("Position Scarcity - Draft Patterns")
    
    # Filter for which positions to show
    all_positions = sorted(df['position'].unique())
    selected_positions_scarcity = st.multiselect(
        "Show Positions", 
        all_positions, 
        default=all_positions,
        placeholder="Select positions to display"
    )
    
    if selected_positions_scarcity:
        # Prepare data for all selected positions
        scarcity_data = []
        
        for pos in selected_positions_scarcity:
            pos_data = df[df['position'] == pos].sort_values('overall_pick')
            for rank, (_, row) in enumerate(pos_data.iterrows()):
                scarcity_data.append({
                    'Position': pos,
                    'Overall_Pick': row['overall_pick'],
                    'Position_Rank': rank + 1,
                    'Player': f"{row['first_name']} {row['last_name']}",
                    'Year': row['year']
                })
        
        scarcity_df = pd.DataFrame(scarcity_data)
        
        # Create scatter plot with all positions
        fig_scarcity = px.scatter(
            scarcity_df,
            x='Overall_Pick',
            y='Position_Rank',
            color='Position',
            title="Position Draft Patterns - When Each Position Gets Picked",
            labels={
                'Overall_Pick': 'Overall Draft Pick', 
                'Position_Rank': 'Position Rank (1st, 2nd, 3rd of that position)',
                'Position': 'Position'
            },
            hover_data=['Player', 'Year']
        )
        
        fig_scarcity.update_layout(
            xaxis_title="Overall Draft Pick",
            yaxis_title="Position Rank (1st, 2nd, 3rd... of position)",
            legend_title="Position"
        )
        
        st.plotly_chart(fig_scarcity, use_container_width=True)
        
        # Position comparison stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Position Comparison Stats")
            comparison_stats = []
            for pos in selected_positions_scarcity:
                pos_picks = df[df['position'] == pos]['overall_pick']
                comparison_stats.append({
                    'Position': pos,
                    'Count': len(pos_picks),
                    'Avg Pick': pos_picks.mean().round(1),
                    'Earliest': pos_picks.min(),
                    'Latest': pos_picks.max()
                })
            
            comparison_df = pd.DataFrame(comparison_stats)
            comparison_df = comparison_df.sort_values('Avg Pick')
            st.dataframe(comparison_df, use_container_width=True)
        
        with col2:
            st.subheader("Position Scarcity Insights")
            st.markdown("""
            **How to read this chart:**
            - **X-axis**: Overall draft pick number
            - **Y-axis**: Position rank (1st QB, 2nd QB, etc.)
            - **Colors**: Different positions
            
            **Key insights:**
            - **Early picks**: Positions that go early have steep curves
            - **Position runs**: When multiple of same position go consecutively
            - **Scarcity**: How quickly position ranks increase vs overall picks
            """)
    else:
        st.info("Select at least one position to see the scarcity analysis.")

def round_analysis_tab(df):
    """Round analysis tab for draft strategy"""
    st.header("📊 Round Analysis - Draft Strategy Tool")
    st.markdown("**Analyze what happened in any round and see position scarcity in real-time**")
    
    # Round selector
    max_round = df['round_number'].max()
    selected_round = st.selectbox(
        "Select Round to Analyze", 
        range(1, max_round + 1),
        index=0,  # Default to Round 1
        help="Choose a round to see what picks were made and analyze position scarcity"
    )
    
    # Calculate how many years are in the filtered data for averaging
    years_in_data = df['year'].nunique()
    
    # Calculate data for the selected round (using filtered data)
    round_data = df[df['round_number'] == selected_round].sort_values('overall_pick')
    
    # Data through the selected round (cumulative) - using filtered data
    data_through_round = df[df['round_number'] <= selected_round]
    
    # Data remaining after this round - using filtered data
    data_remaining = df[df['round_number'] > selected_round]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Position breakdown for this round (strategy-focused)
        st.subheader(f"📋 Round {selected_round} Position Breakdown")
        if not round_data.empty:
            # Position summary
            round_summary = round_data['position'].value_counts().sort_index()
            
            if years_in_data > 1:
                # Show averages when multiple years selected
                st.markdown(f"**Average picks per year (across {years_in_data} years):**")
                
                # Create heat map color coding based on pick frequency
                # Get all possible positions from the full dataset
                all_positions = sorted(df['position'].unique())
                max_picks = max(round_summary.values) / years_in_data if len(round_summary) > 0 else 1
                
                # Create columns for heat map display (always show all positions)
                cols = st.columns(len(all_positions))
                
                for idx, pos in enumerate(all_positions):
                    count = round_summary.get(pos, 0)  # Get count or 0 if position not picked
                    avg_picks = count / years_in_data
                    # Calculate color intensity (0-1 scale)
                    intensity = avg_picks / max_picks if max_picks > 0 else 0
                    
                    # Color scale from light blue to dark red
                    if intensity == 0:
                        color = "#f0f0f0"  # Light gray for zero
                    elif intensity <= 0.2:
                        color = "#e3f2fd"  # Very light blue
                    elif intensity <= 0.4:
                        color = "#bbdefb"  # Light blue
                    elif intensity <= 0.6:
                        color = "#90caf9"  # Medium blue
                    elif intensity <= 0.8:
                        color = "#42a5f5"  # Dark blue
                    else:
                        color = "#1976d2"  # Very dark blue
                    
                    # Display in columns with colored background
                    with cols[idx % 6]:
                        st.markdown(f"""
                        <div style="
                            background-color: {color}; 
                            padding: 10px; 
                            border-radius: 8px; 
                            text-align: center;
                            margin: 2px;
                            border: 1px solid #ddd;
                        ">
                            <strong style="color: {'white' if intensity > 0.6 else 'black'};">{pos}</strong><br>
                            <span style="color: {'white' if intensity > 0.6 else 'black'};">{avg_picks:.1f} picks</span>
                        </div>
                        """, unsafe_allow_html=True)
                

                    
            else:
                # Show totals when single year selected
                st.markdown(f"**Position picks in Round {selected_round}:**")
                
                # Create heat map color coding for single year
                # Get all possible positions from the full dataset
                all_positions = sorted(df['position'].unique())
                max_picks = max(round_summary.values) if len(round_summary) > 0 else 1
                
                # Create columns for heat map display (always show all positions)
                cols = st.columns(len(all_positions))
                
                for idx, pos in enumerate(all_positions):
                    count = round_summary.get(pos, 0)  # Get count or 0 if position not picked
                    # Calculate color intensity (0-1 scale)
                    intensity = count / max_picks if max_picks > 0 else 0
                    
                    # Color scale from light blue to dark red
                    if intensity == 0:
                        color = "#f0f0f0"  # Light gray for zero
                    elif intensity <= 0.2:
                        color = "#e3f2fd"  # Very light blue
                    elif intensity <= 0.4:
                        color = "#bbdefb"  # Light blue
                    elif intensity <= 0.6:
                        color = "#90caf9"  # Medium blue
                    elif intensity <= 0.8:
                        color = "#42a5f5"  # Dark blue
                    else:
                        color = "#1976d2"  # Very dark blue
                    
                    # Display in columns with colored background
                    with cols[idx % 6]:
                        st.markdown(f"""
                        <div style="
                            background-color: {color}; 
                            padding: 10px; 
                            border-radius: 8px; 
                            text-align: center;
                            margin: 2px;
                            border: 1px solid #ddd;
                        ">
                            <strong style="color: {'white' if intensity > 0.6 else 'black'};">{pos}</strong><br>
                            <span style="color: {'white' if intensity > 0.6 else 'black'};">{count} picks</span>
                        </div>
                        """, unsafe_allow_html=True)
                

            
            # Visual position breakdown
            if years_in_data > 1:
                # Create data for all positions, including those with 0 picks
                avg_picks_data = []
                for pos in all_positions:
                    count = round_summary.get(pos, 0)
                    avg_picks_data.append(count / years_in_data)
                
                pos_data = pd.DataFrame({
                    'Position': all_positions,
                    'Avg_Picks_Per_Year': avg_picks_data
                })
                fig_round_pos = px.bar(
                    pos_data,
                    x='Position',
                    y='Avg_Picks_Per_Year',
                    title=f"Round {selected_round} - Avg Picks Per Year",
                    color='Position',
                    labels={'Avg_Picks_Per_Year': 'Average Picks Per Year'}
                )
            else:
                # Create data for all positions, including those with 0 picks
                picks_data = []
                for pos in all_positions:
                    count = round_summary.get(pos, 0)
                    picks_data.append(count)
                
                pos_data = pd.DataFrame({
                    'Position': all_positions,
                    'Picks': picks_data
                })
                fig_round_pos = px.bar(
                    pos_data,
                    x='Position',
                    y='Picks',
                    title=f"Round {selected_round} - Position Picks",
                    color='Position',
                    labels={'Picks': 'Number of Picks'}
                )
            
            fig_round_pos.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_round_pos, use_container_width=True)
        else:
            st.info(f"No data available for Round {selected_round}")
    
    with col2:
        # Strategic insights for the round
        st.subheader(f"🎯 Strategic Insights for Round {selected_round}")
        
        # We'll calculate scarcity data first for the insights
        taken_counts = data_through_round['position'].value_counts()
        remaining_counts = data_remaining['position'].value_counts()
        
        # Create comprehensive scarcity dataframe
        all_positions = df['position'].unique()
        scarcity_data = []
        
        for pos in sorted(all_positions):
            taken = taken_counts.get(pos, 0)
            remaining = remaining_counts.get(pos, 0)
            total = taken + remaining
            pct_taken = (taken / total * 100) if total > 0 else 0
            
            if years_in_data > 1:
                # Show averages per year when multiple years selected
                scarcity_data.append({
                    'Position': pos,
                    'Taken (Avg/Year)': round(taken / years_in_data, 1),
                    'Remaining (Avg/Year)': round(remaining / years_in_data, 1),
                    'Total (Avg/Year)': round(total / years_in_data, 1),
                    '% Taken': f"{pct_taken:.1f}%"
                })
            else:
                # Show totals when single year selected
                scarcity_data.append({
                    'Position': pos,
                    'Taken': taken,
                    'Remaining': remaining,
                    'Total': total,
                    '% Taken': f"{pct_taken:.1f}%"
                })
        
        scarcity_df = pd.DataFrame(scarcity_data)
        
        # Strategic insights columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Most scarce positions (highest % taken)
            # Handle different column names for single vs multiple years
            total_col = 'Total (Avg/Year)' if years_in_data > 1 else 'Total'
            remaining_col = 'Remaining (Avg/Year)' if years_in_data > 1 else 'Remaining'
            
            scarcity_df_sorted = scarcity_df[scarcity_df[total_col] > 0].copy()
            scarcity_df_sorted['pct_taken_num'] = scarcity_df_sorted['% Taken'].str.replace('%', '').astype(float)
            scarcity_df_sorted = scarcity_df_sorted.sort_values('pct_taken_num', ascending=False)
            
            st.markdown("**🔥 Most Scarce Positions:**")
            for _, row in scarcity_df_sorted.head(3).iterrows():
                remaining_val = row[remaining_col]
                remaining_text = f"{remaining_val:.1f} left" if years_in_data > 1 else f"{remaining_val} left"
                st.markdown(f"• **{row['Position']}**: {row['% Taken']} taken ({remaining_text})")
        
        with col2:
            # Best value positions (lowest % taken)
            best_value = scarcity_df_sorted.sort_values('pct_taken_num', ascending=True)
            st.markdown("**💎 Best Value Positions:**")
            for _, row in best_value.head(3).iterrows():
                if row['pct_taken_num'] < 100:  # Don't show completely depleted positions
                    remaining_val = row[remaining_col]
                    remaining_text = f"{remaining_val:.1f} left" if years_in_data > 1 else f"{remaining_val} left"
                    st.markdown(f"• **{row['Position']}**: {row['% Taken']} taken ({remaining_text})")
        
        with col3:
            # Round context
            total_picks_so_far = len(data_through_round)
            total_picks_remaining = len(data_remaining)
            
            st.markdown("**📈 Draft Progress:**")
            if years_in_data > 1:
                st.markdown(f"• **Picks completed**: {total_picks_so_far / years_in_data:.0f} (across {years_in_data} years)")
                st.markdown(f"• **Picks remaining**: {total_picks_remaining / years_in_data:.0f}")
            else:
                st.markdown(f"• **Picks completed**: {total_picks_so_far}")
                st.markdown(f"• **Picks remaining**: {total_picks_remaining}")
            
            if selected_round < max_round:
                next_round_picks = df[df['round_number'] == selected_round + 1]['position'].value_counts()
                if not next_round_picks.empty:
                    top_next_pos = next_round_picks.index[0]
                    next_count = next_round_picks[top_next_pos]
                    if years_in_data > 1:
                        st.markdown(f"• **Next round trend**: {next_count / years_in_data:.1f} {top_next_pos}s in Round {selected_round + 1}")
                    else:
                        st.markdown(f"• **Next round trend**: {next_count} {top_next_pos}s taken in Round {selected_round + 1}")
    
    # Position scarcity table section
    st.subheader(f"📊 Position Scarcity Through Round {selected_round}")
    st.dataframe(scarcity_df, use_container_width=True, hide_index=True)
    
    # Visual representation
    if not scarcity_df.empty:
        # Use appropriate column names based on whether we're showing averages or totals
        if years_in_data > 1:
            y_cols = ['Taken (Avg/Year)', 'Remaining (Avg/Year)']
            color_map = {'Taken (Avg/Year)': '#FF6B6B', 'Remaining (Avg/Year)': '#4ECDC4'}
            y_label = 'Avg Players Per Year'
        else:
            y_cols = ['Taken', 'Remaining']
            color_map = {'Taken': '#FF6B6B', 'Remaining': '#4ECDC4'}
            y_label = 'Number of Players'
        
        fig_scarcity = px.bar(
            scarcity_df,
            x='Position',
            y=y_cols,
            title=f"Position Availability Through Round {selected_round}",
            color_discrete_map=color_map,
            labels={'value': y_label, 'variable': 'Status'}
        )
        fig_scarcity.update_layout(height=400)
        st.plotly_chart(fig_scarcity, use_container_width=True)
    
def pick_analysis_tab(df):
    """Pick analysis tab for draft strategy"""
    st.header("🔢 Pick Analysis - Draft Strategy Tool")
    st.markdown("**Analyze what happened at any pick number and see position scarcity in real-time**")
    
    # Pick selector
    max_pick = df['overall_pick'].max()
    selected_pick = st.selectbox(
        "Select Pick Number to Analyze", 
        range(1, max_pick + 1),
        index=0,  # Default to Pick 1
        help="Choose a pick number to see what picks were made and analyze position scarcity"
    )
    
    # Calculate how many years are in the filtered data for averaging
    years_in_data = df['year'].nunique()
    
    # Calculate data for the selected pick (using filtered data)
    pick_data = df[df['overall_pick'] == selected_pick].sort_values('year')
    
    # Data through the selected pick (cumulative) - using filtered data
    data_through_pick = df[df['overall_pick'] <= selected_pick]
    
    # Data remaining after this pick - using filtered data
    data_remaining = df[df['overall_pick'] > selected_pick]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Position breakdown for this pick (strategy-focused)
        st.subheader(f"📋 Pick #{selected_pick} Position Breakdown")
        if not pick_data.empty:
            # Position summary
            pick_summary = pick_data['position'].value_counts().sort_index()
            
            if years_in_data > 1:
                # Show averages when multiple years selected
                st.markdown(f"**Pick frequency (across {years_in_data} years):**")
                
                # Create heat map color coding based on pick frequency
                # Get all possible positions from the full dataset
                all_positions = sorted(df['position'].unique())
                max_picks = max(pick_summary.values) if len(pick_summary) > 0 else 1
                
                # Create columns for heat map display (always show all positions)
                cols = st.columns(len(all_positions))
                
                for idx, pos in enumerate(all_positions):
                    count = pick_summary.get(pos, 0)  # Get count or 0 if position not picked
                    pick_rate = count / years_in_data * 100
                    # Calculate color intensity (0-1 scale)
                    intensity = count / max_picks if max_picks > 0 else 0
                    
                    # Color scale from light blue to dark red
                    if intensity == 0:
                        color = "#f0f0f0"  # Light gray for zero
                    elif intensity <= 0.2:
                        color = "#e3f2fd"  # Very light blue
                    elif intensity <= 0.4:
                        color = "#bbdefb"  # Light blue
                    elif intensity <= 0.6:
                        color = "#90caf9"  # Medium blue
                    elif intensity <= 0.8:
                        color = "#42a5f5"  # Dark blue
                    else:
                        color = "#1976d2"  # Very dark blue
                    
                    # Display in columns with colored background
                    with cols[idx % 6]:
                        st.markdown(f"""
                        <div style="
                            background-color: {color}; 
                            padding: 10px; 
                            border-radius: 8px; 
                            text-align: center;
                            margin: 2px;
                            border: 1px solid #ddd;
                        ">
                            <strong style="color: {'white' if intensity > 0.6 else 'black'};">{pos}</strong><br>
                            <span style="color: {'white' if intensity > 0.6 else 'black'};">{pick_rate:.0f}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                
            else:
                # Show totals when single year selected
                st.markdown(f"**Position picked at Pick #{selected_pick}:**")
                
                # Create heat map color coding for single year
                # Get all possible positions from the full dataset
                all_positions = sorted(df['position'].unique())
                max_picks = max(pick_summary.values) if len(pick_summary) > 0 else 1
                
                # Create columns for heat map display (always show all positions)
                cols = st.columns(len(all_positions))
                
                for idx, pos in enumerate(all_positions):
                    count = pick_summary.get(pos, 0)  # Get count or 0 if position not picked
                    # Calculate color intensity (0-1 scale)
                    intensity = count / max_picks if max_picks > 0 else 0
                    
                    # Color scale from light blue to dark red
                    if intensity == 0:
                        color = "#f0f0f0"  # Light gray for zero
                    elif intensity <= 0.2:
                        color = "#e3f2fd"  # Very light blue
                    elif intensity <= 0.4:
                        color = "#bbdefb"  # Light blue
                    elif intensity <= 0.6:
                        color = "#90caf9"  # Medium blue
                    elif intensity <= 0.8:
                        color = "#42a5f5"  # Dark blue
                    else:
                        color = "#1976d2"  # Very dark blue
                    
                    # Display in columns with colored background
                    with cols[idx % 6]:
                        st.markdown(f"""
                        <div style="
                            background-color: {color}; 
                            padding: 10px; 
                            border-radius: 8px; 
                            text-align: center;
                            margin: 2px;
                            border: 1px solid #ddd;
                        ">
                            <strong style="color: {'white' if intensity > 0.6 else 'black'};">{pos}</strong><br>
                            <span style="color: {'white' if intensity > 0.6 else 'black'};">{'Yes' if count > 0 else 'No'}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            
            # Visual position breakdown
            if years_in_data > 1:
                # Create data for all positions, including those with 0 picks
                pick_rate_data = []
                for pos in all_positions:
                    count = pick_summary.get(pos, 0)
                    pick_rate_data.append(count / years_in_data * 100)
                
                pos_data = pd.DataFrame({
                    'Position': all_positions,
                    'Pick_Rate': pick_rate_data
                })
                fig_pick_pos = px.bar(
                    pos_data,
                    x='Position',
                    y='Pick_Rate',
                    title=f"Pick #{selected_pick} - Position Pick Rate",
                    color='Position',
                    labels={'Pick_Rate': 'Pick Rate (%)'}
                )
            else:
                # Create data for all positions, including those with 0 picks
                picks_data = []
                for pos in all_positions:
                    count = pick_summary.get(pos, 0)
                    picks_data.append(count)
                
                pos_data = pd.DataFrame({
                    'Position': all_positions,
                    'Picked': picks_data
                })
                fig_pick_pos = px.bar(
                    pos_data,
                    x='Position',
                    y='Picked',
                    title=f"Pick #{selected_pick} - Position Selection",
                    color='Position',
                    labels={'Picked': 'Position Selected (1=Yes, 0=No)'}
                )
            
            fig_pick_pos.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_pick_pos, use_container_width=True)
            
            # Show specific picks made at this position
            if not pick_data.empty:
                st.subheader(f"👤 Players Selected at Pick #{selected_pick}")
                pick_details = pick_data[['year', 'first_name', 'last_name', 'position', 'team_name']].copy()
                pick_details['Player'] = pick_details['first_name'] + ' ' + pick_details['last_name']
                pick_details = pick_details[['year', 'Player', 'position', 'team_name']].rename(columns={
                    'year': 'Year',
                    'position': 'Position', 
                    'team_name': 'Team'
                })
                st.dataframe(pick_details, use_container_width=True, hide_index=True)
        else:
            st.info(f"No data available for Pick #{selected_pick}")
    
    with col2:
        # Strategic insights for the pick
        st.subheader(f"🎯 Strategic Insights for Pick #{selected_pick}")
        
        # We'll calculate scarcity data first for the insights
        taken_counts = data_through_pick['position'].value_counts()
        remaining_counts = data_remaining['position'].value_counts()
        
        # Create comprehensive scarcity dataframe
        all_positions = df['position'].unique()
        scarcity_data = []
        
        for pos in sorted(all_positions):
            taken = taken_counts.get(pos, 0)
            remaining = remaining_counts.get(pos, 0)
            total = taken + remaining
            pct_taken = (taken / total * 100) if total > 0 else 0
            
            if years_in_data > 1:
                # Show averages per year when multiple years selected
                scarcity_data.append({
                    'Position': pos,
                    'Taken (Avg/Year)': round(taken / years_in_data, 1),
                    'Remaining (Avg/Year)': round(remaining / years_in_data, 1),
                    'Total (Avg/Year)': round(total / years_in_data, 1),
                    '% Taken': f"{pct_taken:.1f}%"
                })
            else:
                # Show totals when single year selected
                scarcity_data.append({
                    'Position': pos,
                    'Taken': taken,
                    'Remaining': remaining,
                    'Total': total,
                    '% Taken': f"{pct_taken:.1f}%"
                })
        
        scarcity_df = pd.DataFrame(scarcity_data)
        
        # Strategic insights columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Most scarce positions (highest % taken)
            # Handle different column names for single vs multiple years
            total_col = 'Total (Avg/Year)' if years_in_data > 1 else 'Total'
            remaining_col = 'Remaining (Avg/Year)' if years_in_data > 1 else 'Remaining'
            
            scarcity_df_sorted = scarcity_df[scarcity_df[total_col] > 0].copy()
            scarcity_df_sorted['pct_taken_num'] = scarcity_df_sorted['% Taken'].str.replace('%', '').astype(float)
            scarcity_df_sorted = scarcity_df_sorted.sort_values('pct_taken_num', ascending=False)
            
            st.markdown("**🔥 Most Scarce Positions:**")
            for _, row in scarcity_df_sorted.head(3).iterrows():
                remaining_val = row[remaining_col]
                remaining_text = f"{remaining_val:.1f} left" if years_in_data > 1 else f"{remaining_val} left"
                st.markdown(f"• **{row['Position']}**: {row['% Taken']} taken ({remaining_text})")
        
        with col2:
            # Best value positions (lowest % taken)
            best_value = scarcity_df_sorted.sort_values('pct_taken_num', ascending=True)
            st.markdown("**💎 Best Value Positions:**")
            for _, row in best_value.head(3).iterrows():
                if row['pct_taken_num'] < 100:  # Don't show completely depleted positions
                    remaining_val = row[remaining_col]
                    remaining_text = f"{remaining_val:.1f} left" if years_in_data > 1 else f"{remaining_val} left"
                    st.markdown(f"• **{row['Position']}**: {row['% Taken']} taken ({remaining_text})")
        
        with col3:
            # Pick context
            total_picks_so_far = len(data_through_pick)
            total_picks_remaining = len(data_remaining)
            
            st.markdown("**📈 Draft Progress:**")
            if years_in_data > 1:
                st.markdown(f"• **Picks completed**: {total_picks_so_far / years_in_data:.0f} (across {years_in_data} years)")
                st.markdown(f"• **Picks remaining**: {total_picks_remaining / years_in_data:.0f}")
            else:
                st.markdown(f"• **Picks completed**: {total_picks_so_far}")
                st.markdown(f"• **Picks remaining**: {total_picks_remaining}")
            
            # Show what typically happens at the next few picks
            if selected_pick < max_pick:
                next_picks_data = df[df['overall_pick'].isin(range(selected_pick + 1, min(selected_pick + 4, max_pick + 1)))]
                if not next_picks_data.empty:
                    next_pos_counts = next_picks_data['position'].value_counts()
                    if not next_pos_counts.empty:
                        top_next_pos = next_pos_counts.index[0]
                        next_count = next_pos_counts[top_next_pos]
                        if years_in_data > 1:
                            st.markdown(f"• **Next picks trend**: {next_count / years_in_data:.1f} {top_next_pos}s in next 3 picks")
                        else:
                            st.markdown(f"• **Next picks trend**: {next_count} {top_next_pos}s in next 3 picks")
    
    # Position scarcity table section
    st.subheader(f"📊 Position Scarcity Through Pick #{selected_pick}")
    st.dataframe(scarcity_df, use_container_width=True, hide_index=True)
    
    # Visual representation
    if not scarcity_df.empty:
        # Use appropriate column names based on whether we're showing averages or totals
        if years_in_data > 1:
            y_cols = ['Taken (Avg/Year)', 'Remaining (Avg/Year)']
            color_map = {'Taken (Avg/Year)': '#FF6B6B', 'Remaining (Avg/Year)': '#4ECDC4'}
            y_label = 'Avg Players Per Year'
        else:
            y_cols = ['Taken', 'Remaining']
            color_map = {'Taken': '#FF6B6B', 'Remaining': '#4ECDC4'}
            y_label = 'Number of Players'
        
        fig_scarcity = px.bar(
            scarcity_df,
            x='Position',
            y=y_cols,
            title=f"Position Availability Through Pick #{selected_pick}",
            color_discrete_map=color_map,
            labels={'value': y_label, 'variable': 'Status'}
        )
        fig_scarcity.update_layout(height=400)
        st.plotly_chart(fig_scarcity, use_container_width=True)

def team_analysis_tab(df):
    """Team analysis tab"""
    st.header("👥 Team Analysis")
    
    # Team comparison
    st.subheader("Team Comparison")
    
    # Calculate averages per year to make fair comparisons
    team_years = df.groupby('team_name')['year'].nunique().reset_index(name='years_played')
    team_comparison = df.groupby(['team_name', 'position']).size().reset_index(name='total_picks')
    
    # Merge with years played to calculate averages
    team_comparison = team_comparison.merge(team_years, on='team_name')
    team_comparison['avg_picks_per_year'] = (team_comparison['total_picks'] / team_comparison['years_played']).round(1)
    
    # Create pivot table with averages
    team_comparison_pivot = team_comparison.pivot(index='team_name', columns='position', values='avg_picks_per_year').fillna(0)
    
    # Show years played info
    st.info("📊 **Chart shows average picks per year** to fairly compare teams that played different numbers of years")
    
    col1, col2 = st.columns([2, 1])
    with col2:
        st.subheader("Years Played")
        years_df = team_years.sort_values('years_played', ascending=False)
        st.dataframe(years_df, use_container_width=True, hide_index=True)
    
    with col1:
        # Create heatmap with text annotations
        fig_comparison = px.imshow(
            team_comparison_pivot.values,
            x=team_comparison_pivot.columns,
            y=team_comparison_pivot.index,
            title="Team Position Preferences Comparison (Avg Picks Per Year)",
            color_continuous_scale="Viridis",
            text_auto=True,  # This adds the numbers automatically
            aspect="auto"    # This helps with spacing
        )
        
        # Improve layout and spacing
        fig_comparison.update_layout(
            height=600,  # Make it taller for better spacing
            font=dict(size=12),  # Larger font for readability
            title_font_size=16,
            xaxis_title="Position",
            yaxis_title="Team",
            coloraxis_colorbar=dict(
                title="Avg Picks Per Year",
                title_font_size=12
            )
        )
    
        # Improve text appearance
        fig_comparison.update_traces(
            textfont_size=12,
            textfont_color="white"  # White text for better contrast
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Team drafting patterns
    st.subheader("Team Draft Strategies")
    
    selected_team = st.selectbox("Select Team", sorted(df['team_name'].unique()))
    
    team_data = df[df['team_name'] == selected_team]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Team's position preferences
        team_positions = team_data['position'].value_counts()
        team_pos_df = pd.DataFrame({
            'Position': team_positions.index,
            'Count': team_positions.values
        })
        fig_team_pos = px.bar(
            team_pos_df,
            x='Count',
            y='Position',
            orientation='h',
            title=f"{selected_team} - Position Preferences"
        )
        st.plotly_chart(fig_team_pos, use_container_width=True)
    
    with col2:
        # Team's draft picks by round
        team_rounds = team_data['round_number'].value_counts().sort_index()
        team_rounds_df = pd.DataFrame({
            'Round': team_rounds.index,
            'Picks': team_rounds.values
        })
        fig_team_rounds = px.bar(
            team_rounds_df,
            x='Round',
            y='Picks',
            title=f"{selected_team} - Picks by Round"
        )
        st.plotly_chart(fig_team_rounds, use_container_width=True)
    
    # Recent team picks
    st.subheader(f"{selected_team} - Recent Picks")
    team_recent = team_data.nlargest(10, 'overall_pick')[['overall_pick', 'round_number', 'first_name', 'last_name', 'position', 'nfl_team']]
    st.dataframe(team_recent, use_container_width=True)

def player_lookup_tab(df):
    """Player lookup tab"""
    st.header("🔍 Player Lookup")
    
    # Search functionality
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("Search Player Name")
    
    with col2:
        search_position = st.selectbox("Filter by Position", ["All"] + list(df['position'].unique()))
    
    # Filter players
    filtered_players = df.copy()
    
    if search_term:
        filtered_players = filtered_players[
            (filtered_players['first_name'].str.contains(search_term, case=False, na=False)) |
            (filtered_players['last_name'].str.contains(search_term, case=False, na=False))
        ]
    
    if search_position != "All":
        filtered_players = filtered_players[filtered_players['position'] == search_position]
    
    # Display results
    if not filtered_players.empty:
        st.subheader(f"Found {len(filtered_players)} players")
        
        display_cols = ['overall_pick', 'round_number', 'year', 'first_name', 'last_name', 'position', 'nfl_team', 'team_name']
        st.dataframe(filtered_players[display_cols].sort_values('overall_pick'), use_container_width=True)
        
        # Player draft history chart
        if len(filtered_players) > 0:
            selected_player = st.selectbox(
                "Select Player for Detailed View",
                filtered_players.apply(lambda x: f"{x['first_name']} {x['last_name']} ({x['position']})", axis=1).unique()
            )
            
            if selected_player:
                player_name = selected_player.split(' (')[0]
                first_name, last_name = player_name.split(' ', 1)
                
                player_data = filtered_players[
                    (filtered_players['first_name'] == first_name) & 
                    (filtered_players['last_name'] == last_name)
                ]
                
                if len(player_data) > 1:
                    fig_player = px.line(
                        player_data.sort_values('year'),
                        x='year',
                        y='overall_pick',
                        title=f"{selected_player} - Draft Position Over Time",
                        markers=True
                    )
                    st.plotly_chart(fig_player, use_container_width=True)
    else:
        st.info("No players found matching your search criteria.")

if __name__ == "__main__":
    main()