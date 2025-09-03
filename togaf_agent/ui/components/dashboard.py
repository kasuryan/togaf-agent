"""
Dashboard components for displaying user progress and analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any


def render_dashboard():
    """Render the main dashboard with user analytics and progress."""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    user = st.session_state.current_user
    user_id = user["user_id"]
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">📊 Learning Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # Get user analytics and statistics
    analytics = st.session_state.api_client.get_progress_analytics(user_id)
    statistics = st.session_state.api_client.get_user_statistics(user_id)
    insights = st.session_state.api_client.get_learning_insights(user_id)
    
    if not analytics or not statistics:
        st.warning("Unable to load analytics data. Please try refreshing.")
        return
    
    # Overview metrics
    render_overview_metrics(statistics, analytics)
    
    st.markdown("---")
    
    # Progress visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        render_progress_chart(analytics)
        render_certification_readiness(analytics)
    
    with col2:
        render_learning_velocity(analytics)
        render_study_consistency(analytics)
    
    st.markdown("---")
    
    # Learning insights and recommendations
    if insights:
        render_learning_insights(insights)
    
    st.markdown("---")
    
    # Current learning plan status
    render_current_plan_status(user_id)


def render_overview_metrics(statistics: Dict[str, Any], analytics: Dict[str, Any]):
    """Render overview metrics cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overall_progress = analytics.get("overall_completion", 0)
        st.metric(
            label="📈 Overall Progress",
            value=f"{overall_progress:.1f}%",
            delta=f"+{analytics.get('learning_velocity', 1):.1f}x velocity"
        )
    
    with col2:
        study_sessions = statistics.get("activity", {}).get("total_sessions", 0)
        avg_session = statistics.get("activity", {}).get("average_session_minutes", 0)
        st.metric(
            label="🎯 Study Sessions",
            value=str(study_sessions),
            delta=f"{avg_session:.0f} min avg"
        )
    
    with col3:
        current_streak = statistics.get("activity", {}).get("current_streak", 0)
        st.metric(
            label="🔥 Learning Streak",
            value=f"{current_streak} days",
            delta="Keep it up!" if current_streak > 0 else "Start today!"
        )
    
    with col4:
        topics_studied = statistics.get("progress", {}).get("topics_studied", 0)
        foundation_readiness = analytics.get("foundation_readiness", 0)
        st.metric(
            label="📚 Topics Mastered",
            value=str(topics_studied),
            delta=f"{foundation_readiness:.1%} exam ready"
        )


def render_progress_chart(analytics: Dict[str, Any]):
    """Render progress visualization chart."""
    st.markdown("### 📊 Learning Progress")
    
    # Create progress data
    overall_completion = analytics.get("overall_completion", 0)
    foundation_readiness = analytics.get("foundation_readiness", 0) * 100
    
    progress_data = {
        "Metric": ["Overall Progress", "Foundation Readiness"],
        "Percentage": [overall_completion, foundation_readiness]
    }
    
    df = pd.DataFrame(progress_data)
    
    fig = px.bar(
        df, 
        x="Metric", 
        y="Percentage",
        title="Learning Progress Overview",
        color="Percentage",
        color_continuous_scale="Blues"
    )
    
    fig.update_layout(
        showlegend=False,
        height=300,
        yaxis_range=[0, 100]
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_certification_readiness(analytics: Dict[str, Any]):
    """Render certification readiness gauge."""
    st.markdown("### 🎓 Certification Readiness")
    
    foundation_readiness = analytics.get("foundation_readiness", 0)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = foundation_readiness * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Foundation Level"},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_learning_velocity(analytics: Dict[str, Any]):
    """Render learning velocity indicator."""
    st.markdown("### ⚡ Learning Velocity")
    
    velocity = analytics.get("learning_velocity", 1.0)
    velocity_interpretation = {
        "Very Fast": velocity >= 2.0,
        "Fast": 1.5 <= velocity < 2.0,
        "Moderate": 1.0 <= velocity < 1.5,
        "Steady": 0.5 <= velocity < 1.0,
        "Slow": velocity < 0.5
    }
    
    current_level = next(level for level, condition in velocity_interpretation.items() if condition)
    
    # Create velocity visualization
    velocity_colors = {
        "Very Fast": "#00ff00",
        "Fast": "#7fff00", 
        "Moderate": "#ffff00",
        "Steady": "#ffa500",
        "Slow": "#ff0000"
    }
    
    st.markdown(f"**Current Pace:** {current_level}")
    st.markdown(f"**Velocity Score:** {velocity:.2f}x")
    
    progress_bar_color = velocity_colors.get(current_level, "#ffff00")
    progress_value = min(velocity / 3.0, 1.0)  # Normalize to 0-1 range
    
    st.progress(progress_value)
    
    if velocity < 1.0:
        st.info("💡 Consider shorter, more frequent study sessions to boost your learning velocity!")
    elif velocity > 2.0:
        st.success("🚀 Excellent learning pace! You're making rapid progress!")


def render_study_consistency(analytics: Dict[str, Any]):
    """Render study consistency metrics."""
    st.markdown("### 📅 Study Consistency")
    
    consistency = analytics.get("study_consistency", 0)
    consistency_percentage = consistency * 100
    
    consistency_levels = {
        "Excellent": consistency >= 0.8,
        "Good": 0.6 <= consistency < 0.8,
        "Fair": 0.4 <= consistency < 0.6,
        "Needs Improvement": consistency < 0.4
    }
    
    current_consistency = next(level for level, condition in consistency_levels.items() if condition)
    
    # Consistency visualization
    fig = go.Figure(go.Indicator(
        mode = "number+gauge",
        value = consistency_percentage,
        title = {'text': "Consistency Score"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [0, 40], 'color': "red"},
                {'range': [40, 60], 'color': "yellow"},
                {'range': [60, 80], 'color': "lightgreen"},
                {'range': [80, 100], 'color': "green"}
            ]
        }
    ))
    
    fig.update_layout(height=250)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"**Status:** {current_consistency}")


def render_learning_insights(insights: Dict[str, Any]):
    """Render personalized learning insights."""
    st.markdown("### 🔍 Learning Insights & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💪 Your Strengths")
        strengths = insights.get("focus_areas", {}).get("strengths", [])
        
        if strengths:
            for strength in strengths[:3]:
                st.markdown(f"• ✅ {strength}")
        else:
            st.markdown("• Keep learning to identify your strengths!")
        
        st.markdown("#### 📊 Performance Summary")
        perf_summary = insights.get("performance_summary", {})
        
        for key, value in perf_summary.items():
            display_name = key.replace("_", " ").title()
            st.markdown(f"• **{display_name}:** {value}")
    
    with col2:
        st.markdown("#### 🎯 Areas for Improvement")
        improvements = insights.get("focus_areas", {}).get("improvement_needed", [])
        
        if improvements:
            for area in improvements[:3]:
                st.markdown(f"• 🔄 {area}")
        else:
            st.markdown("• Great job! No major improvement areas identified.")
        
        st.markdown("#### 🚀 Next Priorities")
        priorities = insights.get("focus_areas", {}).get("next_priorities", [])
        
        if priorities:
            for priority in priorities[:3]:
                st.markdown(f"• 📌 {priority}")
        else:
            st.markdown("• Continue with your current learning plan!")
    
    # Learning optimization recommendations
    st.markdown("#### 🎓 Optimization Recommendations")
    optimization = insights.get("learning_optimization", {})
    
    if optimization:
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            session_length = optimization.get("optimal_session_length", "30 minutes")
            st.markdown(f"**Optimal Session Length:** {session_length}")
            
            approach = optimization.get("recommended_approach", "Continue current approach")
            st.markdown(f"**Recommended Approach:** {approach}")
        
        with col_opt2:
            best_times = optimization.get("best_study_times", [])
            if best_times:
                times_str = ", ".join(best_times)
                st.markdown(f"**Best Study Times:** {times_str}")


def render_current_plan_status(user_id: str):
    """Render current learning plan status."""
    st.markdown("### 📚 Current Learning Plan")
    
    # Get current topic
    current_topic = st.session_state.api_client.get_current_topic(user_id)
    
    if current_topic and "message" not in current_topic:
        topic_data = current_topic.get("topic", {})
        plan_progress = current_topic.get("plan_progress", {})
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Current Topic:** {topic_data.get('title', 'Unknown')}")
            st.markdown(f"**Description:** {topic_data.get('description', 'No description available')}")
            
            # Progress bar for current plan
            completion = plan_progress.get("completion_percentage", 0)
            st.progress(completion / 100)
            
            current_idx = plan_progress.get("current_index", 0)
            total_topics = plan_progress.get("total_topics", 1)
            st.markdown(f"**Plan Progress:** {current_idx + 1} of {total_topics} topics ({completion:.1f}% complete)")
        
        with col2:
            if st.button("📖 Study This Topic", use_container_width=True, type="primary"):
                st.session_state.page = "chat"
                st.rerun()
            
            if st.button("✅ Mark Complete", use_container_width=True):
                result = st.session_state.api_client.mark_topic_complete(user_id, topic_data.get("topic_id", ""))
                
                if result and "error" not in result:
                    st.success("Topic marked as complete!")
                    st.rerun()
                else:
                    st.error("Failed to mark topic complete")
            
            if st.button("⏭️ Skip Topic", use_container_width=True):
                result = st.session_state.api_client.skip_topic(user_id, topic_data.get("topic_id", ""))
                
                if result and "error" not in result:
                    st.success("Topic skipped!")
                    st.rerun()
                else:
                    st.error("Failed to skip topic")
    else:
        st.info("No active learning plan found. Create a learning plan to get started!")
        
        if st.button("📚 View Learning Plans", use_container_width=True):
            st.session_state.page = "learning_plan"
            st.rerun()