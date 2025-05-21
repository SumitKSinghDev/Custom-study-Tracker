import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(
    page_title="Custom Study/Work Dashboard",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4CAF50, #45a049);
    }
    .css-1d391kg {
        padding: 1.5rem;
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.95);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .st-emotion-cache-1y4p8pa {
        padding: 2rem;
        border-radius: 15px;
        background-color: rgba(255, 255, 255, 0.95);
    }
    .st-emotion-cache-1wrcr25 {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1rem;
    }
    .st-bw {
        background-color: rgba(255, 255, 255, 0.95) !important;
    }
    h1, h2, h3 {
        color: #1e3d59;
    }
    .stSelectbox label, .stTextInput label {
        color: #1e3d59;
    }
    </style>
""", unsafe_allow_html=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('study_tracker.db')
    c = conn.cursor()
    
    # Create tables with enhanced schema
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  subject TEXT,
                  topic TEXT,
                  video_link TEXT,
                  notes TEXT,
                  duration REAL,
                  completed INTEGER,
                  completion_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  goal_type TEXT,
                  description TEXT,
                  deadline TEXT,
                  completed INTEGER,
                  completion_date TEXT,
                  priority TEXT DEFAULT 'Medium',
                  reminder_days INTEGER DEFAULT 3)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subject_progress
                 (subject TEXT PRIMARY KEY,
                  total_planned_hours REAL,
                  completed_hours REAL,
                  last_updated TEXT)''')
    
    conn.commit()
    conn.close()

def check_notifications():
    """Check for tasks and goals that need attention"""
    conn = sqlite3.connect('study_tracker.db')
    
    # Check for upcoming deadlines (next 3 days)
    upcoming_goals = pd.read_sql_query("""
        SELECT * FROM goals 
        WHERE completed = 0 
        AND date(deadline) <= date('now', '+3 days')
        AND date(deadline) >= date('now')
        ORDER BY deadline
    """, conn)
    
    # Check for overdue tasks
    overdue_tasks = pd.read_sql_query("""
        SELECT * FROM tasks 
        WHERE completed = 0 
        AND date(date) < date('now')
        ORDER BY date
    """, conn)
    
    # Check daily study targets
    today_hours = pd.read_sql_query("""
        SELECT subject, SUM(duration) as hours
        FROM tasks 
        WHERE date = date('now')
        GROUP BY subject
    """, conn)
    
    conn.close()
    
    notifications = []
    
    # Goal notifications
    for _, goal in upcoming_goals.iterrows():
        days_left = (datetime.strptime(goal['deadline'], '%Y-%m-%d').date() - datetime.now().date()).days
        if days_left == 0:
            notifications.append(("🚨", f"Goal due today: {goal['description']}"))
        else:
            notifications.append(("⚠️", f"Goal due in {days_left} days: {goal['description']}"))
    
    # Task notifications
    if not overdue_tasks.empty:
        notifications.append(("📝", f"You have {len(overdue_tasks)} overdue tasks!"))
    
    # Study target notifications
    subject_targets = {}
    for _, row in today_hours.iterrows():
        subject_targets[row['subject']] = 2.0  # Default target of 2 hours per subject
    
    for subject, target in subject_targets.items():
        hours = today_hours[today_hours['subject'] == subject]['hours'].sum() if not today_hours.empty else 0
        if hours < target:
            notifications.append(("📚", f"{subject}: {target-hours:.1f}h remaining for today's target"))
    
    return notifications

init_db()

# Main title
st.title("📚 Custom Study/Work Dashboard")

# Display notifications
notifications = check_notifications()
if notifications:
    with st.sidebar:
        st.markdown("### 🔔 Notifications")
        for icon, msg in notifications:
            st.warning(f"{icon} {msg}")

# Sidebar with navigation
page = st.sidebar.selectbox("Navigate to", ["Daily Planner", "Weekly Planner", "Subject Trackers", "Progress", "Goals"])

# Weekly motivational quote
quotes = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Success is not final, failure is not fatal. - Winston Churchill",
    "Education is the most powerful weapon. - Nelson Mandela"
]
import random
st.sidebar.markdown("---")
st.sidebar.markdown("### 💭 Quote of the Week")
st.sidebar.info(random.choice(quotes))

if page == "Daily Planner":
    st.header("📅 Daily Planner")
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Add new task for today
    with st.form("new_daily_task"):
        st.subheader("Add Task for Today")
        col1, col2 = st.columns(2)
        with col1:
            # Get existing subjects
            conn = sqlite3.connect('study_tracker.db')
            subjects = pd.read_sql_query("SELECT DISTINCT subject FROM subject_progress", conn)
            conn.close()
            
            # Add new subject option
            subject_options = list(subjects['subject']) if not subjects.empty else []
            new_subject = st.text_input("Add New Subject/Work")
            if new_subject and new_subject not in subject_options:
                subject_options.append(new_subject)
            
            subject = st.selectbox("Select Subject/Work", subject_options)
            topic = st.text_input("Topic")
            duration = st.number_input("Duration (hours)", min_value=0.5, max_value=5.0, step=0.5)
        with col2:
            video_link = st.text_input("Video/Resource Link (optional)")
            notes = st.text_area("Notes (optional)", height=100)
        
        submitted = st.form_submit_button("Add Task")
        if submitted:
            conn = sqlite3.connect('study_tracker.db')
            c = conn.cursor()
            
            # If it's a new subject, add it to subject_progress
            if new_subject and new_subject not in subject_options:
                c.execute("""INSERT INTO subject_progress 
                            (subject, total_planned_hours, completed_hours, last_updated)
                            VALUES (?, ?, ?, ?)""",
                         (new_subject, 0.0, 0.0, datetime.now().strftime('%Y-%m-%d')))
            
            c.execute("""INSERT INTO tasks 
                        (date, subject, topic, video_link, notes, duration, completed, completion_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (today, subject, topic, 
                      video_link if video_link else None,
                      notes if notes else None,
                      duration, 0, None))
            
            # Update subject progress
            c.execute("""UPDATE subject_progress 
                        SET completed_hours = completed_hours + ?,
                            last_updated = ?
                        WHERE subject = ?""",
                     (duration, today, subject))
            
            conn.commit()
            conn.close()
            st.success("Task added successfully!")

    # Display today's tasks
    st.subheader("Today's Tasks")
    
    # Get today's tasks
    conn = sqlite3.connect('study_tracker.db')
    today_tasks = pd.read_sql_query("""
        SELECT * FROM tasks 
        WHERE date = ?
        ORDER BY completed, subject
    """, conn, params=(today,))
    
    # Get daily progress
    daily_progress = pd.read_sql_query("""
        SELECT subject, 
               SUM(duration) as total_hours,
               SUM(CASE WHEN completed = 1 THEN duration ELSE 0 END) as completed_hours
        FROM tasks 
        WHERE date = ?
        GROUP BY subject
    """, conn, params=(today,))
    conn.close()

    # Display daily progress
    if not daily_progress.empty:
        st.subheader("📊 Today's Progress")
        
        # Calculate total progress
        total_hours = daily_progress['total_hours'].sum()
        completed_hours = daily_progress['completed_hours'].sum()
        progress_percentage = (completed_hours / total_hours * 100) if total_hours > 0 else 0
        
        # Display overall progress
        st.metric("Overall Progress", f"{completed_hours:.1f}/{total_hours:.1f} hours")
        st.progress(progress_percentage / 100)
        
        # Display progress by subject
        cols = st.columns(len(daily_progress))
        for idx, (_, row) in enumerate(daily_progress.iterrows()):
            with cols[idx]:
                subject_progress = (row['completed_hours'] / row['total_hours'] * 100) if row['total_hours'] > 0 else 0
                st.metric(row['subject'], f"{row['completed_hours']:.1f}/{row['total_hours']:.1f}h")
                st.progress(subject_progress / 100)

    # Display tasks
    if not today_tasks.empty:
        # Group tasks by subject
        for subject in today_tasks['subject'].unique():
            subject_tasks = today_tasks[today_tasks['subject'] == subject]
            
            st.write(f"### {subject}")
            for _, row in subject_tasks.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**Topic:** {row['topic']}")
                    if row['notes']:
                        st.write(f"**Notes:** {row['notes']}")
                    if row['video_link']:
                        st.markdown(f"[📺 Resource]({row['video_link']})")
                with col2:
                    st.write(f"**Duration:** {row['duration']}h")
                with col3:
                    if not row['completed']:
                        if st.button(f"✅", key=f"complete_daily_{row['id']}", help="Mark as Complete"):
                            conn = sqlite3.connect('study_tracker.db')
                            c = conn.cursor()
                            c.execute("""UPDATE tasks 
                                       SET completed = 1, completion_date = ? 
                                       WHERE id = ?""",
                                    (today, row['id']))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    else:
                        st.write("✅ Done")
                with col4:
                    if st.button(f"🗑️", key=f"delete_daily_{row['id']}", help="Delete Task"):
                        conn = sqlite3.connect('study_tracker.db')
                        c = conn.cursor()
                        
                        # First, update the subject progress by subtracting the hours if task was completed
                        if row['completed']:
                            c.execute("""UPDATE subject_progress 
                                       SET completed_hours = completed_hours - ?
                                       WHERE subject = ?""",
                                    (row['duration'], row['subject']))
                        
                        # Then delete the task
                        c.execute("DELETE FROM tasks WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown("---")
    else:
        st.info("No tasks planned for today. Add some tasks to get started!")

elif page == "Weekly Planner":
    st.header("📅 Weekly Planner")
    
    # Add new task
    with st.form("new_task"):
        st.subheader("Add New Task")
        col1, col2 = st.columns(2)
        with col1:
            # Get existing subjects
            conn = sqlite3.connect('study_tracker.db')
            subjects = pd.read_sql_query("SELECT DISTINCT subject FROM subject_progress", conn)
            conn.close()
            
            # Add new subject option
            subject_options = list(subjects['subject']) if not subjects.empty else []
            new_subject = st.text_input("Add New Subject/Work")
            if new_subject and new_subject not in subject_options:
                subject_options.append(new_subject)
            
            subject = st.selectbox("Select Subject/Work", subject_options)
            topic = st.text_input("Topic")
            duration = st.number_input("Duration (hours)", min_value=0.5, max_value=5.0, step=0.5)
        with col2:
            video_link = st.text_input("Video/Resource Link (optional)")
            notes = st.text_area("Notes (optional)", height=100)
        
        submitted = st.form_submit_button("Add Task")
        if submitted:
            conn = sqlite3.connect('study_tracker.db')
            c = conn.cursor()
            
            # If it's a new subject, add it to subject_progress
            if new_subject and new_subject not in subject_options:
                c.execute("""INSERT INTO subject_progress 
                            (subject, total_planned_hours, completed_hours, last_updated)
                            VALUES (?, ?, ?, ?)""",
                         (new_subject, 0.0, 0.0, datetime.now().strftime('%Y-%m-%d')))
            
            c.execute("""INSERT INTO tasks 
                        (date, subject, topic, video_link, notes, duration, completed, completion_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (datetime.now().strftime('%Y-%m-%d'), subject, topic, 
                      video_link if video_link else None,
                      notes if notes else None,
                      duration, 0, None))
            
            # Update subject progress
            c.execute("""UPDATE subject_progress 
                        SET completed_hours = completed_hours + ?,
                            last_updated = ?
                        WHERE subject = ?""",
                     (duration, datetime.now().strftime('%Y-%m-%d'), subject))
            
            conn.commit()
            conn.close()
            st.success("Task added successfully!")

    # Display weekly tasks with filters
    st.subheader("This Week's Tasks")
    
    # Get all subjects for filter
    conn = sqlite3.connect('study_tracker.db')
    all_subjects = pd.read_sql_query("SELECT DISTINCT subject FROM tasks", conn)
    conn.close()
    
    col1, col2 = st.columns(2)
    with col1:
        filter_subject = st.multiselect("Filter by Subject/Work", 
            list(all_subjects['subject']) if not all_subjects.empty else [],
            default=list(all_subjects['subject']) if not all_subjects.empty else [])
    with col2:
        show_completed = st.checkbox("Show Completed Tasks", value=True)
    
    # Construct the query based on filters
    query = """
        SELECT id, date, subject, topic, video_link, notes, duration, completed, completion_date
        FROM tasks 
        WHERE date >= date('now', '-7 days')
        AND subject IN ({})
        {}
        ORDER BY date DESC, subject
    """.format(
        ','.join(['?']*len(filter_subject)) if filter_subject else "''",
        "" if show_completed else "AND completed = 0"
    )
    
    conn = sqlite3.connect('study_tracker.db')
    tasks_df = pd.read_sql_query(query, conn, params=filter_subject if filter_subject else [])
    conn.close()

    if not tasks_df.empty:
        # Format the dataframe for display
        display_df = tasks_df.copy()
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
        display_df['status'] = display_df['completed'].map({0: '⏳ Pending', 1: '✅ Completed'})
        
        # Allow marking tasks as complete
        for idx, row in display_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1])
            with col1:
                st.write(f"**Date:** {row['date']}")
                st.write(f"**Subject:** {row['subject']}")
            with col2:
                st.write(f"**Topic:** {row['topic']}")
                if row['notes']:
                    st.write(f"**Notes:** {row['notes']}")
            with col3:
                st.write(f"**Duration:** {row['duration']}h")
                if row['video_link']:
                    st.markdown(f"[📺 Resource]({row['video_link']})")
            with col4:
                if not row['completed']:
                    if st.button(f"✅", key=f"complete_{row['id']}", help="Mark as Complete"):
                        conn = sqlite3.connect('study_tracker.db')
                        c = conn.cursor()
                        c.execute("""UPDATE tasks 
                                   SET completed = 1, completion_date = ? 
                                   WHERE id = ?""",
                                (datetime.now().strftime('%Y-%m-%d'), row['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
                else:
                    st.write("✅ Done")
            with col5:
                if st.button(f"🗑️", key=f"delete_{row['id']}", help="Delete Task"):
                    conn = sqlite3.connect('study_tracker.db')
                    c = conn.cursor()
                    
                    # First, update the subject progress by subtracting the hours if task was completed
                    if row['completed']:
                        c.execute("""UPDATE subject_progress 
                                   SET completed_hours = completed_hours - ?
                                   WHERE subject = ?""",
                                (row['duration'], row['subject']))
                    
                    # Then delete the task
                    c.execute("DELETE FROM tasks WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No tasks found for the selected filters.")

elif page == "Subject Trackers":
    st.header("📊 Subject Trackers")
    
    # Get all subjects
    conn = sqlite3.connect('study_tracker.db')
    subjects = pd.read_sql_query("SELECT DISTINCT subject FROM tasks", conn)
    conn.close()
    
    subject = st.selectbox("Select Subject/Work", list(subjects['subject']) if not subjects.empty else [])
    
    if subject:
        # Get subject progress
        conn = sqlite3.connect('study_tracker.db')
        progress_df = pd.read_sql_query("""
            SELECT sp.*, 
                   COUNT(t.id) as total_tasks,
                   SUM(t.completed) as completed_tasks
            FROM subject_progress sp
            LEFT JOIN tasks t ON sp.subject = t.subject
            WHERE sp.subject = ?
            GROUP BY sp.subject
        """, conn, params=(subject,))
        
        # Get subject tasks
        tasks_df = pd.read_sql_query("""
            SELECT *
            FROM tasks
            WHERE subject = ?
            ORDER BY date DESC
        """, conn, params=(subject,))
        conn.close()

        if not progress_df.empty:
            # Display subject metrics
            total_hours = progress_df.iloc[0]['completed_hours']
            planned_hours = progress_df.iloc[0]['total_planned_hours']
            total_tasks = progress_df.iloc[0]['total_tasks'] or 0
            completed_tasks = progress_df.iloc[0]['completed_tasks'] or 0
            
            # Calculate progress percentages
            hours_progress = (total_hours / planned_hours) * 100 if planned_hours > 0 else 0
            task_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Hours Completed", f"{total_hours:.1f}/{planned_hours:.1f}")
                st.progress(hours_progress / 100)
            with col2:
                st.metric("Tasks Completed", f"{completed_tasks}/{total_tasks}")
                st.progress(task_progress / 100)
            with col3:
                st.metric("Last Updated", progress_df.iloc[0]['last_updated'])
            
            # Display subject content
            st.subheader("📝 Subject Content")
            
            # Add filters
            show_completed = st.checkbox("Show Completed Items", value=True)
            
            if not tasks_df.empty:
                filtered_df = tasks_df if show_completed else tasks_df[tasks_df['completed'] == 0]
                
                for idx, row in filtered_df.iterrows():
                    with st.expander(f"{row['topic']} ({row['date']})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write("**Notes:**")
                            st.write(row['notes'] if row['notes'] else "No notes added")
                            if row['video_link']:
                                st.markdown(f"**Resource:** [📺 Link]({row['video_link']})")
                        with col2:
                            st.write(f"**Duration:** {row['duration']}h")
                            st.write("**Status:** " + ("✅ Completed" if row['completed'] else "⏳ Pending"))
                            if not row['completed']:
                                if st.button(f"Mark Complete", key=f"complete_subject_{row['id']}"):
                                    conn = sqlite3.connect('study_tracker.db')
                                    c = conn.cursor()
                                    c.execute("""UPDATE tasks 
                                               SET completed = 1, completion_date = ? 
                                               WHERE id = ?""",
                                            (datetime.now().strftime('%Y-%m-%d'), row['id']))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                            if st.button(f"🗑️", key=f"delete_subject_{row['id']}", help="Delete Task"):
                                conn = sqlite3.connect('study_tracker.db')
                                c = conn.cursor()
                                
                                # First, update the subject progress by subtracting the hours if task was completed
                                if row['completed']:
                                    c.execute("""UPDATE subject_progress 
                                               SET completed_hours = completed_hours - ?
                                               WHERE subject = ?""",
                                            (row['duration'], row['subject']))
                                
                                # Then delete the task
                                c.execute("DELETE FROM tasks WHERE id = ?", (row['id'],))
                                conn.commit()
                                conn.close()
                                st.rerun()
            else:
                st.info("No tasks recorded for this subject yet.")
        else:
            st.error("Failed to load subject progress.")
    else:
        st.info("Add a new subject to get started!")

elif page == "Progress":
    st.header("📈 Progress Overview")
    
    # Get overall progress data
    conn = sqlite3.connect('study_tracker.db')
    progress_df = pd.read_sql_query("""
        SELECT sp.*,
               COUNT(t.id) as total_tasks,
               SUM(t.completed) as completed_tasks,
               SUM(CASE WHEN t.completed = 1 THEN t.duration ELSE 0 END) as actual_hours
        FROM subject_progress sp
        LEFT JOIN tasks t ON sp.subject = t.subject
        GROUP BY sp.subject
    """, conn)
    
    # Get daily study hours for the last 30 days
    daily_hours = pd.read_sql_query("""
        SELECT date, subject, SUM(duration) as hours
        FROM tasks
        WHERE date >= date('now', '-30 days')
        GROUP BY date, subject
    """, conn)
    conn.close()

    # Display overall progress
    if not progress_df.empty:
        st.subheader("📊 Subject Progress")
        
        for _, row in progress_df.iterrows():
            subject = row['subject']
            completion_rate = (row['completed_tasks'] / row['total_tasks'] * 100) if row['total_tasks'] > 0 else 0
            hours_progress = (row['actual_hours'] / row['total_planned_hours'] * 100) if row['total_planned_hours'] > 0 else 0
            
            st.write(f"### {subject}")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Task Completion:**")
                st.progress(completion_rate / 100)
                st.write(f"{row['completed_tasks']}/{row['total_tasks']} tasks ({completion_rate:.1f}%)")
            with col2:
                st.write("**Hours Progress:**")
                st.progress(hours_progress / 100)
                st.write(f"{row['actual_hours']:.1f}/{row['total_planned_hours']:.1f} hours ({hours_progress:.1f}%)")
        
        # Create study hours visualization
        if not daily_hours.empty:
            st.subheader("📅 Daily Study Hours (Last 30 Days)")
            daily_hours['date'] = pd.to_datetime(daily_hours['date'])
            
            # Create a stacked bar chart
            fig = px.bar(daily_hours, x='date', y='hours', color='subject', title='Daily Study Hours by Subject',
                        labels={'date': 'Date', 'hours': 'Hours', 'subject': 'Subject'},
                        color_discrete_sequence=px.colors.qualitative.Set3)
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Hours",
                legend_title="Subject",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)

elif page == "Goals":
    st.header("🎯 Goals")
    
    # Add new goal with more options
    with st.form("new_goal"):
        st.subheader("Set New Goal")
        col1, col2 = st.columns(2)
        with col1:
            goal_type = st.selectbox("Goal Type", ["Weekly", "Monthly"])
            description = st.text_area("Goal Description")
            priority = st.select_slider("Priority", options=["Low", "Medium", "High"], value="Medium")
        with col2:
            deadline = st.date_input("Deadline", min_value=datetime.now().date())
            reminder_days = st.number_input("Remind me before (days)", min_value=1, max_value=14, value=3)
            
        submitted = st.form_submit_button("Add Goal")
        if submitted:
            conn = sqlite3.connect('study_tracker.db')
            c = conn.cursor()
            c.execute("""INSERT INTO goals 
                        (goal_type, description, deadline, completed, completion_date, priority, reminder_days)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (goal_type, description, deadline.strftime('%Y-%m-%d'), 0, None, priority, reminder_days))
            conn.commit()
            conn.close()
            st.success("Goal added successfully!")

    # Display active goals with timeline
    st.subheader("📋 Active Goals Timeline")
    
    conn = sqlite3.connect('study_tracker.db')
    goals_df = pd.read_sql_query("""
        SELECT * FROM goals 
        WHERE completed = 0
        ORDER BY deadline
    """, conn)
    
    # Display completed goals
    completed_goals = pd.read_sql_query("""
        SELECT * FROM goals 
        WHERE completed = 1
        ORDER BY completion_date DESC
    """, conn)
    conn.close()

    if not goals_df.empty:
        # Create timeline visualization
        goals_df['deadline'] = pd.to_datetime(goals_df['deadline'])
        goals_df['start_date'] = datetime.now().date()
        
        fig = go.Figure()
        
        colors = {'High': 'rgb(255, 99, 71)', 'Medium': 'rgb(255, 165, 0)', 'Low': 'rgb(144, 238, 144)'}
        
        for idx, row in goals_df.iterrows():
            days_left = (row['deadline'].date() - datetime.now().date()).days
            color = colors.get(row['priority'], 'rgb(144, 238, 144)')
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = days_left,
                domain = {'row': idx, 'column': 0},
                title = {'text': f"{row['description']}<br><sub>{row['goal_type']} Goal</sub>"},
                gauge = {
                    'axis': {'range': [None, 30], 'tickwidth': 1},
                    'bar': {'color': color},
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': row['reminder_days']
                    }
                }
            ))
        
        fig.update_layout(
            grid = {'rows': len(goals_df), 'columns': 1, 'pattern': "independent"},
            height = 150 * len(goals_df),
            showlegend = False,
            margin = dict(t=30, b=30)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Display goals in cards
        for idx, row in goals_df.iterrows():
            deadline = row['deadline'].date()
            days_left = (deadline - datetime.now().date()).days
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{row['goal_type']} Goal:** {row['description']}")
                    st.write(f"**Priority:** {row['priority']}")
                with col2:
                    st.write(f"**Deadline:** {deadline.strftime('%Y-%m-%d')}")
                    if days_left < 0:
                        st.error(f"Overdue by {abs(days_left)} days")
                    elif days_left <= row['reminder_days']:
                        st.warning(f"{days_left} days left")
                    else:
                        st.info(f"{days_left} days left")
                with col3:
                    if st.button(f"Complete", key=f"complete_goal_{row['id']}"):
                        conn = sqlite3.connect('study_tracker.db')
                        c = conn.cursor()
                        c.execute("""UPDATE goals 
                                   SET completed = 1, completion_date = ? 
                                   WHERE id = ?""",
                                (datetime.now().strftime('%Y-%m-%d'), row['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown("---")
    else:
        st.info("No active goals. Add a new goal to get started!")

    # Display completed goals in an expander
    with st.expander("✅ View Completed Goals"):
        if not completed_goals.empty:
            for idx, row in completed_goals.iterrows():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{row['goal_type']} Goal:** {row['description']}")
                    st.write(f"**Completed on:** {row['completion_date']}")
                with col2:
                    if st.button(f"🗑️", key=f"delete_goal_{row['id']}", help="Delete Goal"):
                        conn = sqlite3.connect('study_tracker.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM goals WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown("---")
        else:
            st.info("No completed goals yet.") 