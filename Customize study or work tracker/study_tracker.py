import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib
import os

# Set page configuration
st.set_page_config(
    page_title="Karyaa",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for dark theme styling
st.markdown("""
    <style>
    /* Dark Theme */
    :root {
        --bg-color: linear-gradient(135deg, #1a1f2c 0%, #2d3748 100%);
        --card-bg: rgba(26, 32, 44, 0.95);
        --text-color: #ffffff;
        --shadow: 0 4px 6px rgba(0,0,0,0.2);
        --accent-color: #63b3ed;
        --success-color: #48bb78;
        --warning-color: #f6ad55;
        --danger-color: #fc8181;
        --border-color: #4a5568;
    }

    .main {
        background: var(--bg-color);
        color: var(--text-color);
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--success-color), var(--accent-color));
    }

    .css-1d391kg {
        padding: 1.5rem;
        border-radius: 15px;
        background-color: var(--card-bg);
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }

    .st-emotion-cache-1y4p8pa {
        padding: 2rem;
        border-radius: 15px;
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
    }

    .st-emotion-cache-1wrcr25 {
        background-color: var(--card-bg);
        border-radius: 15px;
        padding: 1rem;
        border: 1px solid var(--border-color);
    }

    .st-bw {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color);
    }

    h1, h2, h3 {
        color: var(--text-color);
    }

    .stSelectbox label, .stTextInput label {
        color: var(--text-color);
    }

    /* Custom styling for buttons */
    .stButton > button {
        background-color: var(--accent-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    /* Custom styling for metrics */
    .stMetric {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid var(--border-color);
    }

    /* Custom styling for expanders */
    .streamlit-expanderHeader {
        background-color: var(--card-bg) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--card-bg);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--accent-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-color);
        opacity: 0.8;
    }
    </style>
""", unsafe_allow_html=True)

def get_db_path(username):
    """Get the database path for a specific user"""
    # Create users directory if it doesn't exist
    if not os.path.exists('users'):
        os.makedirs('users')
    return f'users/{username}_study_tracker.db'

def init_user_db(username):
    """Initialize database for a specific user"""
    conn = sqlite3.connect('study_tracker.db')
    c = conn.cursor()
    
    # Create tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  subject TEXT,
                  topic TEXT,
                  video_link TEXT,
                  notes TEXT,
                  duration REAL,
                  completed INTEGER DEFAULT 0,
                  completion_date TEXT)''')
    
    # Create goals table
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  goal_type TEXT,
                  description TEXT,
                  deadline TEXT,
                  completed INTEGER DEFAULT 0,
                  completion_date TEXT,
                  priority TEXT,
                  reminder_days INTEGER)''')
    
    # Create subject_progress table
    c.execute('''CREATE TABLE IF NOT EXISTS subject_progress
                 (subject TEXT PRIMARY KEY,
                  total_planned_hours REAL DEFAULT 0,
                  completed_hours REAL DEFAULT 0,
                  last_updated TEXT)''')
    
    conn.commit()
    conn.close()

def init_auth_db():
    """Initialize the authentication database"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY,
                  password_hash TEXT,
                  created_at TEXT)''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash the password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    """Register a new user"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    
    # Check if username already exists
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False
    
    # Add new user
    password_hash = hash_password(password)
    c.execute("""INSERT INTO users (username, password_hash, created_at)
                 VALUES (?, ?, ?)""",
              (username, password_hash, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    
    # Initialize user's database
    init_user_db(username)
    return True

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    
    password_hash = hash_password(password)
    c.execute("""SELECT username FROM users 
                 WHERE username = ? AND password_hash = ?""",
              (username, password_hash))
    
    result = c.fetchone()
    conn.close()
    return result is not None

# Initialize authentication database
init_auth_db()

# Authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Login/Register form
if not st.session_state.authenticated:
    st.title("📚 Welcome to Karyaa")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if verify_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Register")
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                elif register_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists")

else:
    # Main application code
    def get_db_connection():
        """Get database connection for the current user"""
        return sqlite3.connect(get_db_path(st.session_state.username))

    def check_notifications():
        """Check for tasks and goals that need attention"""
        conn = get_db_connection()
        
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

    # Initialize user's database
    init_user_db(st.session_state.username)

    # Main title with username
    st.title(f"📚 {st.session_state.username}'s Study/Work Dashboard")

    # Logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    # Display notifications
    notifications = check_notifications()
    if notifications:
        with st.sidebar:
            st.markdown("### 🔔 Notifications")
            for icon, msg in notifications:
                st.warning(f"{icon} {msg}")

    # Sidebar with navigation
    page = st.sidebar.selectbox("Navigate to", ["Daily Planner", "Weekly Planner", "Goals"])

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
                    try:
                        c.execute("""INSERT INTO subject_progress 
                                    (subject, total_planned_hours, completed_hours, last_updated)
                                    VALUES (?, ?, ?, ?)""",
                                 (new_subject, 0.0, 0.0, today))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        # Subject already exists, ignore
                        pass
                
                # Add the task
                c.execute("""INSERT INTO tasks 
                            (date, subject, topic, video_link, notes, duration, completed, completion_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                         (today, subject, topic, 
                          video_link if video_link else None,
                          notes if notes else None,
                          duration, 0, None))
                
                # Update subject progress
                c.execute("""UPDATE subject_progress 
                            SET total_planned_hours = total_planned_hours + ?,
                                last_updated = ?
                            WHERE subject = ?""",
                         (duration, today, subject))
                
                conn.commit()
                conn.close()
                st.success("Task added successfully!")
                st.rerun()

        # Display today's tasks
        st.subheader("Today's Tasks")
        
        # Get today's tasks
        conn = get_db_connection()
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
                                conn = get_db_connection()
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
                            conn = get_db_connection()
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
                conn = get_db_connection()
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
                conn = get_db_connection()
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
        conn = get_db_connection()
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
        
        conn = get_db_connection()
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
                            conn = get_db_connection()
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
                        conn = get_db_connection()
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
                conn = get_db_connection()
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
        
        conn = get_db_connection()
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
                            conn = get_db_connection()
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
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute("DELETE FROM goals WHERE id = ?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("No completed goals yet.") 