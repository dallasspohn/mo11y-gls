"""
Relationship Timeline Visualization
Creates beautiful visualizations of your relationship with Mo11y
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from enhanced_memory import EnhancedMemory


class RelationshipTimeline:
    """Create visualizations of relationship growth and milestones"""
    
    def __init__(self, memory: EnhancedMemory):
        self.memory = memory
    
    def create_interaction_timeline(self, days_back: int = 365) -> go.Figure:
        """Create a timeline of interactions over time"""
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count, 
                   AVG(importance_score) as avg_importance
            FROM episodic_memories
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (cutoff_date.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return self._empty_figure("No interaction data yet")
        
        dates = [row[0] for row in rows]
        counts = [row[1] for row in rows]
        importance = [row[2] for row in rows]
        
        fig = go.Figure()
        
        # Add interaction count line
        fig.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines+markers',
            name='Daily Interactions',
            line=dict(color='#667eea', width=2),
            marker=dict(size=8)
        ))
        
        # Add importance overlay
        fig.add_trace(go.Scatter(
            x=dates,
            y=[i * max(counts) for i in importance],
            mode='lines',
            name='Avg Importance',
            line=dict(color='#f5576c', width=1, dash='dash'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Interaction Timeline",
            xaxis_title="Date",
            yaxis_title="Number of Interactions",
            yaxis2=dict(
                title="Average Importance",
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_sentiment_heatmap(self, days_back: int = 90) -> go.Figure:
        """Create a heatmap of sentiment over time (deprecated - emotional tracking removed)"""
        # Emotional tracking has been removed - return empty figure
        return self._empty_figure("Sentiment tracking is not available in business mode")
    
    def create_milestone_timeline(self) -> go.Figure:
        """Create a timeline of relationship milestones"""
        relationship_summary = self.memory.get_relationship_summary()
        milestones = relationship_summary.get("milestones", [])
        
        if not milestones:
            return self._empty_figure("No milestones yet")
        
        # Prepare data
        milestone_data = []
        for i, milestone in enumerate(milestones):
            milestone_data.append({
                'Date': milestone['timestamp'],
                'Milestone': milestone['description'],
                'Type': milestone['type'],
                'Significance': milestone['significance']
            })
        
        df = pd.DataFrame(milestone_data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        fig = go.Figure()
        
        # Add milestone markers
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['Date']],
                y=[row['Significance']],
                mode='markers+text',
                marker=dict(
                    size=row['Significance'] * 20 + 10,
                    color=row['Significance'],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=[row['Milestone'][:30] + "..." if len(row['Milestone']) > 30 else row['Milestone']],
                textposition="top center",
                name=row['Type']
            ))
        
        fig.update_layout(
            title="Relationship Milestones",
            xaxis_title="Date",
            yaxis_title="Significance",
            hovermode='closest',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def create_personality_radar(self, personality_traits: Dict) -> go.Figure:
        """Create a radar chart of personality traits"""
        if not personality_traits:
            return self._empty_figure("No personality data")
        
        categories = list(personality_traits.keys())
        values = [trait['value'] for trait in personality_traits.values()]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[c.title() for c in categories],
            fill='toself',
            name='Current Personality',
            line_color='#667eea'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Personality Radar",
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def create_memory_importance_distribution(self) -> go.Figure:
        """Create a distribution of memory importance scores"""
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT importance_score FROM episodic_memories")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return self._empty_figure("No memories yet")
        
        importance_scores = [row[0] for row in rows]
        
        fig = px.histogram(
            x=importance_scores,
            nbins=20,
            title="Memory Importance Distribution",
            labels={'x': 'Importance Score', 'y': 'Count'},
            color_discrete_sequence=['#667eea']
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def _empty_figure(self, message: str) -> go.Figure:
        """Create an empty figure with a message"""
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=message,
            showarrow=False,
            font=dict(size=16, color='gray')
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400
        )
        return fig
