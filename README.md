# Custom Study/Work Tracker Dashboard

A comprehensive dashboard application built with Streamlit to help you track your study or work progress, manage tasks, and achieve your goals.

## 🌟 Features

### 📅 Daily Planner
- Add and manage tasks for the current day
- Track daily progress across different subjects/work items
- Visual progress indicators for each subject
- Real-time progress updates
- Task completion tracking

### 📊 Weekly Planner
- Plan and organize tasks for the entire week
- Filter tasks by subject/work item
- Track completion status
- Add notes and resource links
- Delete or modify tasks

### 📈 Subject Trackers
- Monitor progress for each subject/work item
- View detailed statistics and metrics
- Track completed hours and tasks
- Visual progress indicators
- Subject-specific task management

### 📊 Progress Overview
- Comprehensive progress visualization
- Daily study/work hours tracking
- Subject-wise progress breakdown
- Interactive charts and graphs
- 30-day progress history

### 🎯 Goals Management
- Set weekly and monthly goals
- Priority-based goal tracking
- Deadline management
- Progress visualization
- Goal completion tracking

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd study-tracker
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## 💻 Usage

1. Start the application:
```bash
streamlit run study_tracker.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically https://karyaa.streamlit.app/)

3. Start using the dashboard:
   - Add your subjects/work items
   - Create daily and weekly tasks
   - Set goals and track progress
   - Monitor your achievements

## 📋 Database Structure

The application uses SQLite with the following tables:

### Tasks Table
- id (Primary Key)
- date
- subject
- topic
- video_link
- notes
- duration
- completed
- completion_date

### Goals Table
- id (Primary Key)
- goal_type
- description
- deadline
- completed
- completion_date
- priority
- reminder_days

### Subject Progress Table
- subject (Primary Key)
- total_planned_hours
- completed_hours
- last_updated

## 🛠️ Requirements

- Python 3.11.8
- streamlit==1.32.0
- pandas==2.2.0
- plotly==5.18.0
- numpy==1.26.4
- pillow>=10.1.0

## 📱 Features in Detail

### Daily Planner
- Add tasks for the current day
- Track progress in real-time
- Subject-wise organization
- Progress visualization
- Task completion tracking

### Weekly Planner
- 7-day task management
- Subject filtering
- Task status tracking
- Resource management
- Flexible task organization

### Subject Trackers
- Individual subject progress
- Detailed statistics
- Task management
- Progress visualization
- Performance metrics

### Progress Overview
- Overall progress tracking
- Subject-wise breakdown
- Historical data analysis
- Visual progress indicators
- Performance trends

### Goals Management
- Goal setting and tracking
- Priority management
- Deadline tracking
- Progress visualization
- Achievement tracking

## 🔧 Customization

The dashboard can be customized by:
1. Modifying the CSS styles in the code
2. Adding new features to the existing modules
3. Customizing the database schema
4. Adding new visualization types
5. Modifying the notification system

## 📝 Notes

- The application uses SQLite for data storage
- All data is stored locally
- Progress is tracked in real-time
- Notifications are generated automatically
- Data is preserved between sessions

## 🤝 Contributing

Feel free to contribute to this project by:
1. Forking the repository
2. Creating a new branch
3. Making your changes
4. Submitting a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 
