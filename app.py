# import streamlit as st
# import sqlite3
# import hashlib # For password hashing
# import pandas as pd
# from datetime import datetime

# # --- 1. Database Setup ---
# DB_NAME = 'project_tracker.db'

# def init_db():
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()

#     # Create Users table
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )
#     ''')

#     # Create Projects table
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS projects (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER NOT NULL,
#             project_name TEXT NOT NULL,
#             description TEXT,
#             start_date DATE,
#             end_date DATE,
#             budget REAL,
#             FOREIGN KEY (user_id) REFERENCES users (id)
#         )
#     ''')

#     # Create Tasks table
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS tasks (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             project_id INTEGER NOT NULL,
#             task_name TEXT NOT NULL,
#             status TEXT DEFAULT 'Not Started',
#             progress_percentage INTEGER DEFAULT 0,
#             assigned_to TEXT,
#             due_date DATE,
#             FOREIGN KEY (project_id) REFERENCES projects (id)
#         )
#     ''')
#     conn.commit()
#     conn.close()

# # Ensure database is initialized when app starts
# init_db()

# # --- Hash Password Function ---
# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# # --- Database Interaction Functions ---

# # @st.cache_resource removed
# def get_db_connection():
#     """Returns a new database connection."""
#     return sqlite3.connect(DB_NAME, check_same_thread=False)

# def add_user(username, password):
#     conn = get_db_connection()
#     c = conn.cursor()
#     try:
#         hashed_password = hash_password(password)
#         c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
#         conn.commit()
#         # Retrieve the newly inserted user_id
#         user_id = c.lastrowid # This gets the ID of the last inserted row
#         return user_id # Return the user ID on success
#     except sqlite3.IntegrityError:
#         st.error("Username already exists. Please choose a different one.")
#         return False
#     finally:
#         conn.close()

# def verify_user(username, password):
#     conn = get_db_connection()
#     c = conn.cursor()
#     c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
#     user_data = c.fetchone()
#     conn.close()
#     if user_data:
#         user_id, stored_password = user_data
#         if stored_password == hash_password(password):
#             return user_id
#     return None

# def add_project(user_id, project_name, description, start_date, end_date, budget):
#     conn = get_db_connection()
#     c = conn.cursor()
#     try:
#         c.execute("INSERT INTO projects (user_id, project_name, description, start_date, end_date, budget) VALUES (?, ?, ?, ?, ?, ?)",
#                   (user_id, project_name, description, start_date, end_date, budget))
#         conn.commit()
#         return True
#     except Exception as e:
#         st.error(f"Error adding project: {e}")
#         return False
#     finally:
#         conn.close()

# def get_projects_by_user(user_id):
#     conn = get_db_connection()
#     df = pd.read_sql_query("SELECT id, project_name, description, start_date, end_date, budget FROM projects WHERE user_id = ?", conn, params=(user_id,))
#     conn.close()
#     return df

# def update_project(project_id, project_name, description, start_date, end_date, budget):
#     conn = get_db_connection()
#     c = conn.cursor()
#     c.execute("UPDATE projects SET project_name=?, description=?, start_date=?, end_date=?, budget=? WHERE id=?",
#               (project_name, description, start_date, end_date, budget, project_id))
#     conn.commit()
#     conn.close()

# def delete_project(project_id):
#     conn = get_db_connection()
#     c = conn.cursor()
#     # Delete associated tasks first due to foreign key constraint
#     c.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
#     c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
#     conn.commit()
#     conn.close()

# def add_task(project_id, task_name, status, progress_percentage, assigned_to, due_date):
#     conn = get_db_connection()
#     c = conn.cursor()
#     try:
#         c.execute("INSERT INTO tasks (project_id, task_name, status, progress_percentage, assigned_to, due_date) VALUES (?, ?, ?, ?, ?, ?)",
#                   (project_id, task_name, status, progress_percentage, assigned_to, due_date))
#         conn.commit()
#         return True
#     except Exception as e:
#         st.error(f"Error adding task: {e}")
#         return False
#     finally:
#         conn.close()

# def get_tasks_by_project(project_id):
#     conn = get_db_connection()
#     df = pd.read_sql_query("SELECT id, task_name, status, progress_percentage, assigned_to, due_date FROM tasks WHERE project_id = ?", conn, params=(project_id,))
#     conn.close()
#     return df

# def update_task(task_id, task_name, status, progress_percentage, assigned_to, due_date):
#     conn = get_db_connection()
#     c = conn.cursor()
#     c.execute("UPDATE tasks SET task_name=?, status=?, progress_percentage=?, assigned_to=?, due_date=? WHERE id=?",
#               (task_name, status, progress_percentage, assigned_to, due_date, task_id))
#     conn.commit()
#     conn.close()

# def delete_task(task_id):
#     conn = get_db_connection()
#     c = conn.cursor()
#     c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
#     conn.commit()
#     conn.close()

# # --- 2. Streamlit App Layout ---

# st.set_page_config(layout="wide", page_title="Civil Eng Project Tracker")
# st.title("Civil Engineering Project Tracker")

# # Initialize session state variables
# if 'logged_in' not in st.session_state:
#     st.session_state.logged_in = False
# if 'username' not in st.session_state:
#     st.session_state.username = None
# if 'user_id' not in st.session_state:
#     st.session_state.user_id = None
# if 'page' not in st.session_state:
#     st.session_state.page = 'login'
# if 'has_projects' not in st.session_state:
#     st.session_state.has_projects = False # To check if user has projects
# if 'selected_project_id' not in st.session_state:
#     st.session_state.selected_project_id = None
# if 'selected_project_name' not in st.session_state:
#     st.session_state.selected_project_name = None

# # --- User Authentication (Login/Register) ---
# def login_page():
#     st.subheader("Login / Register")
#     tab1, tab2 = st.tabs(["Login", "Register"])

#     with tab1:
#         st.write("### Existing User Login")
#         username = st.text_input("Username", key="login_username")
#         password = st.text_input("Password", type="password", key="login_password")
#         # In login_page() -> with tab1:
#     if st.button("Login"):
#         user_id = verify_user(username, password)
#         if user_id:
#             st.session_state.logged_in = True
#             st.session_state.username = username
#             st.session_state.user_id = user_id
#             st.session_state.page = 'dashboard' # Change from 'projects' to 'dashboard'
#             st.rerun()
#         else:
#             st.error("Invalid username or password")

#     with tab2:
#         st.write("### New User Registration")
#         new_username = st.text_input("Choose Username", key="reg_username")
#         new_password = st.text_input("Create Password", type="password", key="reg_password")
#         confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
#         if st.button("Register"):
#             if new_password == confirm_password:
#                 # Modified line: Get the user_id back from add_user
#                 registered_user_id = add_user(new_username, new_password)
#                 if registered_user_id:
#                     st.success("Account created successfully! Logging you in...")
#                     # Automatically log in the user
#                     st.session_state.logged_in = True
#                     st.session_state.username = new_username
#                     st.session_state.user_id = registered_user_id
#                     st.session_state.page = 'dashboard' # Or 'projects' if no dashboard
#                     st.rerun() # Force rerun to show dashboard
#                 # else (add_user returned None due to error, e.g., username exists),
#                 # the st.error message from add_user will already be displayed.
#             else:
#                 st.error("Passwords do not match.")

# def dashboard_page():
#     st.subheader(f"Welcome to your Civil Engineering Project Tracker, {st.session_state.username}!")

#     st.markdown("""
#     This application helps you manage and track the progress of your various civil engineering projects.
#     You can add new projects, define tasks within them, and update their progress.
#     """)

#     # Fetch projects to check if the user has any
#     projects_df = get_projects_by_user(st.session_state.user_id)

#     if not projects_df.empty:
#         st.session_state.has_projects = True
#         st.success("You have active projects! Click 'My Projects' in the sidebar to view and manage them.")
#         st.write("### Your Project Summary:")
#         # Display a quick summary of active projects
#         st.info(f"You are currently tracking **{len(projects_df)}** projects.")
#         # Optional: Display a few most recent projects or quick stats
#         st.dataframe(projects_df.head(3), use_container_width=True, hide_index=True) # Show top 3
#     else:
#         st.session_state.has_projects = False
#         st.info("You don't have any projects yet. Let's get started!")
#         if st.button("Create Your First Project"):
#             st.session_state.page = 'projects'
#             st.rerun()

#     st.markdown("---")
#     st.write("### Quick Actions")
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("Go to My Projects"):
#             st.session_state.page = 'projects'
#             st.rerun()
#     with col2:
#         # Maybe add another quick action like 'View Overdue Tasks' once implemented
#         pass # Placeholder

# # --- Main Application Pages ---
# def projects_page():
#     st.subheader(f"Welcome, {st.session_state.username}! Your Projects")

#     projects_df = get_projects_by_user(st.session_state.user_id)

#     if not projects_df.empty:
#         st.write("### Your Current Projects")
#         st.dataframe(projects_df, use_container_width=True, hide_index=True)

#         st.write("### Select a Project to Manage Tasks or Edit/Delete")
#         col1, col2 = st.columns([0.7, 0.3])
#         with col1:
#             selected_project_id_from_df = st.selectbox(
#                 "Select Project",
#                 options=projects_df['id'].tolist(),
#                 format_func=lambda x: projects_df[projects_df['id'] == x]['project_name'].iloc[0],
#                 key="select_project_to_manage"
#             )
#         with col2:
#             st.markdown("---") # Visual separator
#             if st.button("Manage Tasks for Selected Project"):
#                 st.session_state.selected_project_id = selected_project_id_from_df
#                 st.session_state.selected_project_name = projects_df[projects_df['id'] == selected_project_id_from_df]['project_name'].iloc[0]
#                 st.session_state.page = 'tasks'
#                 st.rerun()

#         # Edit/Delete Project Forms
#         st.markdown("---")
#         st.write("### Add / Edit / Delete Projects")
#         project_action = st.radio("Choose action", ("Add New Project", "Edit Selected Project", "Delete Selected Project"), horizontal=True)

#         if project_action == "Add New Project":
#             with st.form("add_project_form"):
#                 project_name = st.text_input("Project Name (e.g., Bridge Construction Phase 1)")
#                 description = st.text_area("Description")
#                 start_date = st.date_input("Start Date", value=datetime.today())
#                 end_date = st.date_input("End Date", value=datetime.today())
#                 budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f")
#                 submitted = st.form_submit_button("Add Project")
#                 if submitted:
#                     if add_project(st.session_state.user_id, project_name, description, start_date, end_date, budget):
#                         st.success(f"Project '{project_name}' added!")
#                         st.rerun()

#         elif project_action == "Edit Selected Project":
#             if selected_project_id_from_df:
#                 selected_project_data = projects_df[projects_df['id'] == selected_project_id_from_df].iloc[0]
#                 with st.form("edit_project_form"):
#                     st.write(f"Editing Project: **{selected_project_data['project_name']}**")
#                     edited_name = st.text_input("Project Name", value=selected_project_data['project_name'])
#                     edited_description = st.text_area("Description", value=selected_project_data['description'])
#                     edited_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_project_data['start_date']))
#                     edited_end_date = st.date_input("End Date", value=pd.to_datetime(selected_project_data['end_date']))
#                     edited_budget = st.number_input("Budget ($)", value=float(selected_project_data['budget']), format="%.2f")
#                     submitted_edit = st.form_submit_button("Update Project")
#                     if submitted_edit:
#                         update_project(selected_project_id_from_df, edited_name, edited_description, edited_start_date, edited_end_date, edited_budget)
#                         st.success("Project updated successfully!")
#                         st.rerun()
#             else:
#                 st.warning("Please select a project to edit.")

#         elif project_action == "Delete Selected Project":
#             if selected_project_id_from_df:
#                 st.error(f"Deleting Project: **{projects_df[projects_df['id'] == selected_project_id_from_df]['project_name'].iloc[0]}**")
#                 if st.button("Confirm Delete Project", type="secondary"):
#                     delete_project(selected_project_id_from_df)
#                     st.success("Project deleted successfully!")
#                     st.rerun()
#             else:
#                 st.warning("Please select a project to delete.")

#     else:
#         st.info("You don't have any projects yet. Use the 'Add New Project' option below to create one.")
#         with st.form("add_project_form_empty"): # Form for adding project when no projects exist
#                 project_name = st.text_input("Project Name (e.g., Road Resurfacing Phase A)")
#                 description = st.text_area("Description")
#                 start_date = st.date_input("Start Date", value=datetime.today(), key="start_date_empty")
#                 end_date = st.date_input("End Date", value=datetime.today(), key="end_date_empty")
#                 budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f", key="budget_empty")
#                 submitted = st.form_submit_button("Add Project")
#                 if submitted:
#                     if add_project(st.session_state.user_id, project_name, description, start_date, end_date, budget):
#                         st.success(f"Project '{project_name}' added!")
#                         st.rerun()


# def tasks_page():
#     if not st.session_state.selected_project_id:
#         st.warning("No project selected. Please go to 'Projects' to select one.")
#         st.session_state.page = 'projects'
#         st.rerun() # Immediately go back to projects page

#     st.subheader(f"Tasks for Project: {st.session_state.selected_project_name}")

#     tasks_df = get_tasks_by_project(st.session_state.selected_project_id)

#     if not tasks_df.empty:
#         st.write("### Current Tasks")
#         # Calculate overall project progress
#         overall_progress = tasks_df['progress_percentage'].mean() if not tasks_df.empty else 0
#         st.metric(label="Overall Project Progress", value=f"{overall_progress:.1f}%")
#         st.progress(overall_progress / 100.0)

#         st.dataframe(tasks_df, use_container_width=True, hide_index=True)

#         st.write("### Select a Task to Edit or Delete")
#         selected_task_id_from_df = st.selectbox(
#             "Select Task",
#             options=tasks_df['id'].tolist(),
#             format_func=lambda x: tasks_df[tasks_df['id'] == x]['task_name'].iloc[0],
#             key="select_task_to_manage"
#         )
#     else:
#         st.info("No tasks added for this project yet.")
#         selected_task_id_from_df = None # Ensure it's None if no tasks

#     st.markdown("---")
#     st.write("### Add / Edit / Delete Tasks")
#     task_action = st.radio("Choose task action", ("Add New Task", "Edit Selected Task", "Delete Selected Task"), horizontal=True)

#     status_options = ['Not Started', 'In Progress', 'On Hold', 'Completed', 'Cancelled']

#     if task_action == "Add New Task":
#         with st.form("add_task_form"):
#             task_name = st.text_input("Task Name (e.g., Foundation Excavation)")
#             status = st.selectbox("Status", options=status_options)
#             progress_percentage = st.slider("Progress (%)", 0, 100, 0)
#             assigned_to = st.text_input("Assigned To (Optional)")
#             due_date = st.date_input("Due Date", value=datetime.today())
#             submitted = st.form_submit_button("Add Task")
#             if submitted:
#                 if add_task(st.session_state.selected_project_id, task_name, status, progress_percentage, assigned_to, due_date):
#                     st.success(f"Task '{task_name}' added!")
#                     st.rerun()

#     elif task_action == "Edit Selected Task":
#         if selected_task_id_from_df:
#             selected_task_data = tasks_df[tasks_df['id'] == selected_task_id_from_df].iloc[0]
#             with st.form("edit_task_form"):
#                 st.write(f"Editing Task: **{selected_task_data['task_name']}**")
#                 edited_task_name = st.text_input("Task Name", value=selected_task_data['task_name'])
#                 edited_status = st.selectbox("Status", options=status_options, index=status_options.index(selected_task_data['status']))
#                 edited_progress_percentage = st.slider("Progress (%)", 0, 100, int(selected_task_data['progress_percentage']))
#                 edited_assigned_to = st.text_input("Assigned To (Optional)", value=selected_task_data['assigned_to'] if pd.notna(selected_task_data['assigned_to']) else "")
#                 edited_due_date = st.date_input("Due Date", value=pd.to_datetime(selected_task_data['due_date']))
#                 submitted_edit = st.form_submit_button("Update Task")
#                 if submitted_edit:
#                     update_task(selected_task_id_from_df, edited_task_name, edited_status, edited_progress_percentage, edited_assigned_to, edited_due_date)
#                     st.success("Task updated successfully!")
#                     st.rerun()
#         else:
#             st.warning("Please select a task to edit.")

#     elif task_action == "Delete Selected Task":
#         if selected_task_id_from_df:
#             st.error(f"Deleting Task: **{tasks_df[tasks_df['id'] == selected_task_id_from_df]['task_name'].iloc[0]}**")
#             if st.button("Confirm Delete Task", type="secondary"):
#                 delete_task(selected_task_id_from_df)
#                 st.success("Task deleted successfully!")
#                 st.rerun()
#         else:
#             st.warning("Please select a task to delete.")

# # --- Sidebar Navigation ---

# with st.sidebar:
#     # --- Logo Placement ---
#     st.image("logo.jpg", use_container_width=True, caption="Youceatech Logo") # Add your logo here!
#     st.markdown("---") # Separator after logo
#     st.header("Navigation")
#     if st.session_state.logged_in:
#         st.write(f"Logged in as: **{st.session_state.username}**")
#         if st.button("Dashboard"): # New button
#             st.session_state.page = 'dashboard'
#             st.session_state.selected_project_id = None
#             st.rerun()
#         if st.button("My Projects"):
#             st.session_state.page = 'projects'
#             st.session_state.selected_project_id = None # Clear selected project when going back to projects
#             st.rerun()
#         if st.session_state.selected_project_id:
#             if st.button(f"Tasks for {st.session_state.selected_project_name}"):
#                 st.session_state.page = 'tasks'
#                 st.rerun()
#         st.markdown("---") # Separator before contact links
#         if st.button("Logout"):
#             st.session_state.logged_in = False
#             st.session_state.username = None
#             st.session_state.user_id = None
#             st.session_state.page = 'login'
#             st.success("Logged out successfully.")
#             st.rerun()
#     else:
#         st.write("Please log in or register.")
    
#     # --- Contact Links (Added Section) ---
#     st.markdown("---") # Another separator
#     st.subheader("Connect with the Developer")
#     st.markdown(
#         """
        
#         [Portfolio/Website](https://ceaytech.quarto.pub/)  
#         """
#     )
#     # Optional: Add icons (requires knowing Font Awesome class names)
#     st.markdown(
#         """
#         <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
#         <div style="display: flex; gap: 10px;">
#             <a href="https://github.com/Seek-Techs" target="_blank" style="color: grey; text-decoration: none;">
#                 <i class="fab fa-github"></i> GitHub
#             </a>
#             <a href="https://www.linkedin.com/in/sikiru-yusuff-olatunji" target="_blank" style="color: grey; text-decoration: none;">
#                 <i class="fab fa-linkedin"></i> LinkedIn
#             </a>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )

#     st.markdown("---") # Final separator
#     st.markdown("Developed by: Yusuff Olatunji Sikiru") # Optional copyright/credit
#     st.markdown("Version 1.0") # Optional version info

# # --- Page Routing ---
# if st.session_state.page == 'login':
#     login_page()
# elif st.session_state.page == 'dashboard' and st.session_state.logged_in: # New route
#     dashboard_page()
# elif st.session_state.page == 'projects' and st.session_state.logged_in:
#     projects_page()
# elif st.session_state.page == 'tasks' and st.session_state.logged_in:
#     tasks_page()
# else: # Fallback if somehow not logged in but on a restricted page
#     st.session_state.logged_in = False
#     st.session_state.username = None
#     st.session_state.user_id = None
#     st.session_state.page = 'login'
#     st.rerun()









import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# --- 1. Database Setup ---
DB_NAME = 'project_tracker.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            description TEXT,
            start_date DATE,
            end_date DATE,
            budget REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            status TEXT DEFAULT 'Not Started',
            progress_percentage INTEGER DEFAULT 0,
            assigned_to TEXT,
            due_date DATE,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def add_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed_password = hash_password(password)
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        user_id = c.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different one.")
        return None
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        user_id, stored_password = user_data
        if stored_password == hash_password(password):
            return user_id
    return None

def add_project(user_id, project_name, description, start_date, end_date, budget):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO projects (user_id, project_name, description, start_date, end_date, budget) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, project_name, description, start_date, end_date, budget))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding project: {e}")
        return False
    finally:
        conn.close()

def get_projects_by_user(user_id):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, project_name, description, start_date, end_date, budget FROM projects WHERE user_id = ? ORDER BY id ASC", conn, params=(user_id,))
    conn.close()
    if not df.empty:
        # Add a user-specific sequential ID
        df['User Project ID'] = range(1, len(df) + 1)
        # Reorder columns to put the new ID first (optional)
        df = df[['User Project ID', 'id', 'project_name', 'description', 'start_date', 'end_date', 'budget']]
    return df

def update_project(project_id, project_name, description, start_date, end_date, budget):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE projects SET project_name=?, description=?, start_date=?, end_date=?, budget=? WHERE id=?",
              (project_name, description, start_date, end_date, budget, project_id))
    conn.commit()
    conn.close()

def delete_project(project_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,)) # Delete associated tasks first
    c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def add_task(project_id, task_name, status, progress_percentage, assigned_to, due_date):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tasks (project_id, task_name, status, progress_percentage, assigned_to, due_date) VALUES (?, ?, ?, ?, ?, ?)",
                  (project_id, task_name, status, progress_percentage, assigned_to, due_date))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding task: {e}")
        return False
    finally:
        conn.close()

def get_tasks_by_project(project_id):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, task_name, status, progress_percentage, assigned_to, due_date FROM tasks WHERE project_id = ? ORDER BY id ASC", conn, params=(project_id,))
    conn.close()
    if not df.empty:
        # Add a project-specific sequential ID for tasks
        df['Task No.'] = range(1, len(df) + 1)
        # Reorder columns (optional)
        df = df[['Task No.', 'id', 'task_name', 'status', 'progress_percentage', 'assigned_to', 'due_date']]
    return df

def update_task(task_id, task_name, status, progress_percentage, assigned_to, due_date):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET task_name=?, status=?, progress_percentage=?, assigned_to=?, due_date=? WHERE id=?",
              (task_name, status, progress_percentage, assigned_to, due_date, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- Streamlit App Layout ---

st.set_page_config(layout="wide", page_title="Civil Eng Project Tracker")

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = None
if 'selected_project_name' not in st.session_state:
    st.session_state.selected_project_name = None
# No need for 'page' in session_state if using tabs for main nav

# --- User Authentication (Login/Register) ---
def login_register_section(): # Renamed to avoid confusion with overall app logic
    st.title("Civil Engineering Project Tracker")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.write("### Existing User Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user_id = verify_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = user_id
                st.rerun() # Rerun to switch to main app
            else:
                st.error("Invalid username or password")

    with tab2:
        st.write("### New User Registration")
        new_username = st.text_input("Choose Username", key="reg_username")
        new_password = st.text_input("Create Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Register"):
            if new_password == confirm_password:
                registered_user_id = add_user(new_username, new_password)
                if registered_user_id:
                    st.success("Account created successfully! Logging you in...")
                    st.session_state.logged_in = True
                    st.session_state.username = new_username
                    st.session_state.user_id = registered_user_id
                    st.rerun() # Rerun to switch to main app
            else:
                st.error("Passwords do not match.")

# --- Main Application Pages ---
def dashboard_page_content(): # Content for the Dashboard tab
    st.subheader(f"Welcome to your Civil Engineering Project Tracker, {st.session_state.username}!")

    st.markdown("""
    This application helps you manage and track the progress of your various civil engineering projects.
    You can add new projects, define tasks within them, and update their progress.
    """)

    projects_df = get_projects_by_user(st.session_state.user_id)

    if not projects_df.empty:
        st.success(f"You are currently tracking **{len(projects_df)}** projects. View them in the 'My Projects' tab.")
        st.write("### Quick Overview of Your Projects:")
        st.dataframe(projects_df.head(3), use_container_width=True, hide_index=True)
    else:
        st.info("You don't have any projects yet. Go to the 'My Projects' tab to create your first one!")

    st.markdown("---")
    st.write("### Quick Actions")
    # You could add specific quick actions here, e.g., 'View Overdue Tasks'
    # For now, just a placeholder.

def projects_page_content(): # Content for the My Projects tab
    st.subheader(f"Your Projects, {st.session_state.username}")

    projects_df = get_projects_by_user(st.session_state.user_id)

    if not projects_df.empty:
        st.write("### Your Current Projects")
        st.dataframe(projects_df, use_container_width=True, hide_index=True)

        st.write("### Select a Project to Manage Tasks or Edit/Delete")
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            # Use the actual 'id' for the options, but display 'User Project ID' + 'project_name' in format_func
            selected_project_id_from_df = st.selectbox(
                "Select Project",
                options=projects_df['id'].tolist(), # Still select by database ID
                format_func=lambda x: f"P{projects_df[projects_df['id'] == x]['User Project ID'].iloc[0]} - {projects_df[projects_df['id'] == x]['project_name'].iloc[0]}",
                key="select_project_to_manage"
            )
        with col2:
            st.markdown("---") # Visual separator
            # When using tabs, selecting a project and then clicking a tab is natural
            # So, we'll just set the selected_project_id and let the Tasks tab handle it
            st.session_state.selected_project_id = selected_project_id_from_df # Set this explicitly
            st.session_state.selected_project_name = projects_df[projects_df['id'] == selected_project_id_from_df]['project_name'].iloc[0]


        # Edit/Delete Project Forms
        st.markdown("---")
        st.write("### Add / Edit / Delete Projects")
        project_action = st.radio("Choose action", ("Add New Project", "Edit Selected Project", "Delete Selected Project"), horizontal=True)

        if project_action == "Add New Project":
            with st.form("add_project_form"):
                project_name = st.text_input("Project Name (e.g., Bridge Construction Phase 1)")
                description = st.text_area("Description")
                start_date = st.date_input("Start Date", value=datetime.today())
                end_date = st.date_input("End Date", value=datetime.today())
                budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f")
                submitted = st.form_submit_button("Add Project")
                if submitted:
                    if add_project(st.session_state.user_id, project_name, description, start_date, end_date, budget):
                        st.success(f"Project '{project_name}' added!")
                        st.rerun()

        elif project_action == "Edit Selected Project":
            if selected_project_id_from_df:
                selected_project_data = projects_df[projects_df['id'] == selected_project_id_from_df].iloc[0]
                with st.form("edit_project_form"):
                    st.write(f"Editing Project: **{selected_project_data['project_name']}**")
                    edited_name = st.text_input("Project Name", value=selected_project_data['project_name'])
                    edited_description = st.text_area("Description", value=selected_project_data['description'])
                    edited_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_project_data['start_date']))
                    edited_end_date = st.date_input("End Date", value=pd.to_datetime(selected_project_data['end_date']))
                    edited_budget = st.number_input("Budget ($)", value=float(selected_project_data['budget']), format="%.2f")
                    submitted_edit = st.form_submit_button("Update Project")
                    if submitted_edit:
                        update_project(selected_project_id_from_df, edited_name, edited_description, edited_start_date, edited_end_date, edited_budget)
                        st.success("Project updated successfully!")
                        st.rerun()
            else:
                st.warning("Please select a project to edit.")

        elif project_action == "Delete Selected Project":
            if selected_project_id_from_df:
                st.error(f"Deleting Project: **{projects_df[projects_df['id'] == selected_project_id_from_df]['project_name'].iloc[0]}**")
                if st.button("Confirm Delete Project", type="secondary"):
                    delete_project(selected_project_id_from_df)
                    st.success("Project deleted successfully!")
                    st.rerun()
            else:
                st.warning("Please select a project to delete.")

    else:
        st.info("You don't have any projects yet. Use the 'Add New Project' option below to create one.")
        with st.form("add_project_form_empty"):
                project_name = st.text_input("Project Name (e.g., Road Resurfacing Phase A)")
                description = st.text_area("Description")
                start_date = st.date_input("Start Date", value=datetime.today(), key="start_date_empty")
                end_date = st.date_input("End Date", value=datetime.today(), key="end_date_empty")
                budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f", key="budget_empty")
                submitted = st.form_submit_button("Add Project")
                if submitted:
                    if add_project(st.session_state.user_id, project_name, description, start_date, end_date, budget):
                        st.success(f"Project '{project_name}' added!")
                        st.rerun()

def tasks_page_content(): # Content for the Tasks tab
    if not st.session_state.selected_project_id:
        st.warning("No project selected. Please go to 'My Projects' tab and select one to manage tasks.")
        return # Exit early if no project selected

    st.subheader(f"Tasks for Project: {st.session_state.selected_project_name}")

    tasks_df = get_tasks_by_project(st.session_state.selected_project_id)

    selected_task_id_from_df = None # Initialize outside conditional blocks

    if not tasks_df.empty:
        st.write("### Current Tasks")
        overall_progress = tasks_df['progress_percentage'].mean() if not tasks_df.empty else 0
        st.metric(label="Overall Project Progress", value=f"{overall_progress:.1f}%")
        st.progress(overall_progress / 100.0)

        st.dataframe(tasks_df, use_container_width=True, hide_index=True)

        st.write("### Select a Task to Edit or Delete")
        # THIS IS THE CORRECT SELECTBOX FOR DISPLAYING USER-FRIENDLY ID
        selected_task_id_from_df = st.selectbox(
            "Select Task",
            options=tasks_df['id'].tolist(), # Still select by database ID
            format_func=lambda x: f"T{tasks_df[tasks_df['id'] == x]['Task No.'].iloc[0]} - {tasks_df[tasks_df['id'] == x]['task_name'].iloc[0]}",
            key="select_task_to_manage"
        )
    else:
        st.info("No tasks added for this project yet.")
        # No selected_task_id_from_df if tasks_df is empty, already initialized to None

    st.markdown("---")
    st.write("### Add / Edit / Delete Tasks")
    task_action = st.radio("Choose task action", ("Add New Task", "Edit Selected Task", "Delete Selected Task"), horizontal=True)
    status_options = ['Not Started', 'In Progress', 'On Hold', 'Completed', 'Cancelled']

    if task_action == "Add New Task":
        with st.form("add_task_form"):
            task_name = st.text_input("Task Name (e.g., Foundation Excavation)")
            status = st.selectbox("Status", options=status_options)
            progress_percentage = st.slider("Progress (%)", 0, 100, 0)
            assigned_to = st.text_input("Assigned To (Optional)")
            due_date = st.date_input("Due Date", value=datetime.today())
            submitted = st.form_submit_button("Add Task")
            if submitted:
                if add_task(st.session_state.selected_project_id, task_name, status, progress_percentage, assigned_to, due_date):
                    st.success(f"Task '{task_name}' added!")
                    st.rerun()

    elif task_action == "Edit Selected Task":
        # Check if a task is selected before trying to edit
        if selected_task_id_from_df: # This variable is correctly set by the *first* selectbox
            selected_task_data = tasks_df[tasks_df['id'] == selected_task_id_from_df].iloc[0]
            with st.form("edit_task_form"):
                st.write(f"Editing Task: **{selected_task_data['task_name']}**")
                edited_task_name = st.text_input("Task Name", value=selected_task_data['task_name'])
                edited_status = st.selectbox("Status", options=status_options, index=status_options.index(selected_task_data['status']))
                edited_progress_percentage = st.slider("Progress (%)", 0, 100, int(selected_task_data['progress_percentage']))
                edited_assigned_to = st.text_input("Assigned To (Optional)", value=selected_task_data['assigned_to'] if pd.notna(selected_task_data['assigned_to']) else "")
                edited_due_date = st.date_input("Due Date", value=pd.to_datetime(selected_task_data['due_date']))
                submitted_edit = st.form_submit_button("Update Task")
                if submitted_edit:
                    update_task(selected_task_id_from_df, edited_task_name, edited_status, edited_progress_percentage, edited_assigned_to, edited_due_date)
                    st.success("Task updated successfully!")
                    st.rerun()
        else:
            st.warning("Please select a task to edit.") # This message appears if no tasks or no task selected

    elif task_action == "Delete Selected Task":
        # Check if a task is selected before trying to delete
        if selected_task_id_from_df: # This variable is correctly set by the *first* selectbox
            st.error(f"Deleting Task: **{tasks_df[tasks_df['id'] == selected_task_id_from_df]['task_name'].iloc[0]}**")
            if st.button("Confirm Delete Task", type="secondary"):
                delete_task(selected_task_id_from_df)
                st.success("Task deleted successfully!")
                st.rerun()
        else:
            st.warning("Please select a task to delete.") # This message appears if no tasks or no task selected
# --- Main App Logic ---
if not st.session_state.logged_in:
    login_register_section() # Show login/register if not logged in
else:
    # --- Top Navigation Tabs ---
    st.title("Civil Engineering Project Tracker") # Main title visible after login

    # User Info and Logout in a header/info bar
    st.info(f"Welcome, **{st.session_state.username}**! You are logged in. "
            f"Click the 'Logout' button at the end of the tabs if you wish to exit.")

    # Create the tabs for main navigation
    tab_dashboard, tab_projects, tab_tasks, tab_logout = st.tabs(["Dashboard", "My Projects", "Tasks", "Logout"])

    with tab_dashboard:
        dashboard_page_content()
    with tab_projects:
        projects_page_content()
    with tab_tasks:
        tasks_page_content()
    with tab_logout:
        st.write("Are you sure you want to log out?")
        if st.button("Confirm Logout", key="confirm_logout_tab"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.selected_project_id = None
            st.session_state.selected_project_name = None
            st.success("Logged out successfully.")
            st.rerun()

    # --- Optional: Sidebar for Logo and Contact Info ---
    with st.sidebar:
        # --- Logo Placement ---
        st.image("logo.jpg", use_container_width=True, caption="Civil Engineering Solutions")
        st.markdown("---")

        st.subheader("Connect with the Developer")
        st.markdown(
            """
            
            [Portfolio/Website](https://ceaytech.quarto.pub/)  
            """
        )
        # Optional: Add icons (requires knowing Font Awesome class names)
        st.markdown(
            """
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <div style="display: flex; gap: 10px;">
                <a href="https://github.com/Seek-Techs" target="_blank" style="color: grey; text-decoration: none;">
                    <i class="fab fa-github"></i> GitHub
                </a>
                <a href="https://www.linkedin.com/in/sikiru-yusuff-olatunji" target="_blank" style="color: grey; text-decoration: none;">
                    <i class="fab fa-linkedin"></i> LinkedIn
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown("Developed by: Yusuff Olatunji Sikiru")
        st.markdown("Version 1.0")