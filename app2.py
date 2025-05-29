import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import io # For CSV export
import base64 # Not explicitly needed with st.download_button's data parameter
import plotly.express as px # For visualizations
import plotly.graph_objects as go # For more complex plots

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
    # CORRECTED: Added DEFAULT 'Medium' to task_priority
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            status TEXT DEFAULT 'Not Started',
            task_priority TEXT DEFAULT 'Medium', -- CORRECTED: Added default value
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

def add_task(project_id, task_name, status, task_priority, progress_percentage, assigned_to, due_date):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tasks (project_id, task_name, status, task_priority, progress_percentage, assigned_to, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (project_id, task_name, status, task_priority, progress_percentage, assigned_to, due_date))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding task: {e}")
        return False
    finally:
        conn.close()

def get_tasks_by_project(project_id):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, task_name, status, task_priority, progress_percentage, assigned_to, due_date FROM tasks WHERE project_id = ? ORDER BY id ASC", conn, params=(project_id,))
    conn.close()

    if not df.empty:
        # Convert due_date to datetime objects for comparison
        df['due_date'] = pd.to_datetime(df['due_date'])
        # Get today's date without time for fair comparison
        today = pd.to_datetime(datetime.now().date())

        # Determine if task is overdue (past due_date AND not completed/cancelled)
        df['Is Overdue'] = (df['due_date'] < today) & (~df['status'].isin(['Completed', 'Cancelled']))

        # Add a project-specific sequential ID for tasks
        df['Task No.'] = range(1, len(df) + 1)
        # Reorder columns to include 'task_priority' and 'Is Overdue' in display
        df = df[['Task No.', 'id', 'task_name', 'status', 'task_priority', 'progress_percentage', 'assigned_to', 'due_date', 'Is Overdue']]
    return df

# CORRECTED: Added task_priority parameter to update_task
def update_task(task_id, task_name, status, task_priority, progress_percentage, assigned_to, due_date):
    conn = get_db_connection()
    c = conn.cursor()
    # CORRECTED: Included task_priority in the UPDATE statement
    c.execute("UPDATE tasks SET task_name=?, status=?, task_priority=?, progress_percentage=?, assigned_to=?, due_date=? WHERE id=?",
              (task_name, status, task_priority, progress_percentage, assigned_to, due_date, task_id))
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
if 'current_view' not in st.session_state: # New session state for top navigation
    st.session_state.current_view = 'Dashboard' # Default view after login
# NEW FLAGS FOR QUICK ACTIONS
if 'show_add_project_form' not in st.session_state:
    st.session_state.show_add_project_form = False
if 'show_add_task_form' not in st.session_state:
    st.session_state.show_add_task_form = False
if 'filter_tasks_status' not in st.session_state:
    st.session_state.filter_tasks_status = 'All' # Default to 'All'

# --- User Authentication (Login/Register) ---
def login_register_section():
    st.title("Civil Engineering Project Tracker")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.write("### Existing User Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user_id = verify_user(username, password)
            if user_id:
                st.toast("Login successfully!", icon='🎉')
                import time
                time.sleep(.5)
                st.balloons()
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = user_id
                st.session_state.current_view = 'Dashboard' # Set default view on login
                st.rerun()
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
                    st.toast("Account created successfully! successfully!", icon='🎉')
                    import time
                    time.sleep(.5)
                    st.balloons()
                    st.session_state.logged_in = True
                    st.session_state.username = new_username
                    st.session_state.user_id = registered_user_id
                    st.session_state.current_view = 'Dashboard' # Set default view on registration
                    st.rerun()
            else:
                st.error("Passwords do not match.")

# --- Content Functions ---
def dashboard_page_content():
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

        # --- Data Visualization: Project Progress (Example) ---
        st.markdown("---")
        st.write("### Project Progress at a Glance")

        tasks_all_projects_df = pd.DataFrame()
        for project_id in projects_df['id']:
            tasks_for_project = get_tasks_by_project(project_id)
            if not tasks_for_project.empty:
                tasks_for_project['project_name'] = projects_df[projects_df['id'] == project_id]['project_name'].iloc[0]
                tasks_all_projects_df = pd.concat([tasks_all_projects_df, tasks_for_project])

        # CORRECTED: Check tasks_all_projects_df for 'progress_percentage' and emptiness
        if not tasks_all_projects_df.empty and 'progress_percentage' in tasks_all_projects_df.columns:
            # Calculate average progress per project
            project_progress_summary = tasks_all_projects_df.groupby('project_name')['progress_percentage'].mean().reset_index()
            fig = px.bar(project_progress_summary, x='project_name', y='progress_percentage',
                         title='Average Task Progress Per Project',
                         labels={'project_name': 'Project Name', 'progress_percentage': 'Average Progress (%)'},
                         color='progress_percentage', color_continuous_scale=px.colors.sequential.Tealgrn)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add some tasks to your projects to see progress visualizations!")

        st.markdown("---")
        st.write("### Overdue Task Summary Across All Projects")

        all_user_tasks = pd.DataFrame()
        for project_id in projects_df['id']:
            tasks_for_project = get_tasks_by_project(project_id) # This now includes 'Is Overdue'
            if not tasks_for_project.empty:
                tasks_for_project['project_name'] = projects_df[projects_df['id'] == project_id]['project_name'].iloc[0]
                all_user_tasks = pd.concat([all_user_tasks, tasks_for_project])

        if not all_user_tasks.empty:
            overdue_all_count = all_user_tasks[all_user_tasks['Is Overdue']].shape[0]
            if overdue_all_count > 0:
                st.error(f"🚨 You have a total of **{overdue_all_count}** tasks overdue across all your projects!")
                st.write("Here are the top 5 most urgent overdue tasks:")
                # Sort by due date to show most urgent first
                overdue_summary_df = all_user_tasks[all_user_tasks['Is Overdue']].sort_values(by='due_date', ascending=True)
                st.dataframe(overdue_summary_df[['project_name', 'task_name', 'due_date', 'assigned_to']].head(5), use_container_width=True, hide_index=True)
            else:
                st.success("🎉 Great! No overdue tasks across all your projects.")
        else:
            st.info("No tasks added yet to calculate overdue status.")

    else:
        st.info("You don't have any projects yet. Go to the 'My Projects' tab to create your first one!")

    st.markdown("---")
    st.write("### Quick Actions")
    # Layout for quick action buttons
    qa_cols = st.columns(4) # Adjust number of columns as needed

    with qa_cols[0]:
        if st.button("➕ New Project", use_container_width=True, key="qa_new_project_btn"):
            st.session_state.current_view = 'Projects'
            st.session_state.show_add_project_form = True # Flag to immediately show add form on Projects page
            st.rerun()

    with qa_cols[1]:
        if st.button("➕ New Task", use_container_width=True, key="qa_new_task_btn"):
            st.session_state.current_view = 'Tasks'
            st.session_state.show_add_task_form = True # Flag to immediately show add form on Tasks page
            st.rerun()

    with qa_cols[2]:
        if st.button("⚠️ View Overdue Tasks", use_container_width=True, key="qa_overdue_tasks_btn"):
            st.session_state.current_view = 'Tasks'
            st.session_state.filter_tasks_status = 'Overdue' # Set a filter for the tasks page
            st.rerun()

    with qa_cols[3]:
        if st.button("📄 Generate Report", use_container_width=True, key="qa_generate_report_btn"):
            st.session_state.current_view = 'Reports'
            st.rerun()

    # Make sure to handle `show_add_project_form`, `show_add_task_form`,
    # and `filter_tasks_status` in your `projects_page_content()` and `tasks_page_content()`
    # functions respectively. For example, in `tasks_page_content()`:
    # if 'filter_tasks_status' in st.session_state and st.session_state.filter_tasks_status == 'Overdue':
    #     # Apply filter to your tasks_df
    #     filtered_df = tasks_df[tasks_df['Is Overdue'] == True]
    #     # Clear the flag after use so it doesn't stick
    #     del st.session_state.filter_tasks_status

def projects_page_content():
    st.subheader(f"Your Projects, {st.session_state.username}")

    projects_df = get_projects_by_user(st.session_state.user_id)

    # Determine initial radio button selection based on flag
    initial_project_action_index = 0 # Default to "Add New Project"
    if st.session_state.show_add_project_form:
        initial_project_action_index = 0 # "Add New Project" is typically the first option (index 0)
        st.session_state.show_add_project_form = False # CLEAR THE FLAG after acting on it


    # Main UI for projects
    if not projects_df.empty:
        st.write("### Your Current Projects")
        st.dataframe(projects_df, use_container_width=True, hide_index=True)

        # --- Export to CSV for Projects ---
        # This part should be moved here, inside the check for non-empty projects,
        # so you don't offer to export an empty dataframe.
        csv_export = projects_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Projects as CSV",
            data=csv_export,
            file_name=f"projects_data_{st.session_state.username}.csv",
            mime="text/csv",
            key="download_projects_csv_with_data" # Unique key (this key should be fine as it's not a form_submit_button)
        )


        st.write("### Select a Project to Manage Tasks or Edit/Delete")
        # Ensure we have options for selectbox if projects_df is filtered or empty after search
        selected_project_id_from_df = st.selectbox(
            "Select Project",
            options=projects_df['id'].tolist(),
            format_func=lambda x: f"P{projects_df[projects_df['id'] == x]['User Project ID'].iloc[0]} - {projects_df[projects_df['id'] == x]['project_name'].iloc[0]}",
            key="select_project_to_manage"
        )

        if selected_project_id_from_df:
            # Set session state for task page
            st.session_state.selected_project_id = selected_project_id_from_df
            st.session_state.selected_project_name = projects_df[projects_df['id'] == selected_project_id_from_df]['project_name'].iloc[0]
            st.success(f"Selected project: **{st.session_state.selected_project_name}**. Go to 'Tasks' tab to manage it.")
        else:
            st.session_state.selected_project_id = None
            st.session_state.selected_project_name = None
            st.info("Please select a project to proceed with actions.")


        st.markdown("---")
        st.write("### Project Actions") # More generic title

        # This is the main radio button for Add/Edit/Delete
        project_action = st.radio(
            "Choose action",
            ("Add New Project", "Edit Selected Project", "Delete Selected Project"),
            horizontal=True,
            index=initial_project_action_index, # Use the determined index
            key="project_action_radio_main" # UNIQUE KEY IS CRITICAL! This radio button's key is fine.
        )

        # Handle actions based on the selected radio button
        if project_action == "Add New Project":
            # Form for adding a new project
            with st.form("add_project_form"):
                project_name = st.text_input("Project Name (e.g., Road Resurfacing Phase A)", key="add_project_name")
                description = st.text_area("Description", key="add_project_desc")
                start_date = st.date_input("Start Date", value=datetime.today(), key="add_project_start_date")
                end_date = st.date_input("End Date", value=datetime.today(), key="add_project_end_date")
                budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f", key="add_project_budget")
                submitted = st.form_submit_button("Add Project") # REMOVED key="add_project_submit"
                if submitted:
                    if add_project(st.session_state.user_id, project_name, description, start_date, end_date, budget):
                        st.success(f"Project '{project_name}' added!")
                        st.rerun()
                    else:
                        st.error("Failed to add project. Please check input.")

        elif project_action == "Edit Selected Project":
            # Form for editing selected project
            if selected_project_id_from_df:
                project_to_edit = projects_df[projects_df['id'] == selected_project_id_from_df].iloc[0]
                with st.form("edit_project_form"):
                    st.write(f"Editing Project: **{project_to_edit['project_name']}**")
                    edited_name = st.text_input("Project Name", value=project_to_edit['project_name'], key="edit_project_name")
                    edited_description = st.text_area("Description", value=project_to_edit['description'], key="edit_project_desc")
                    # Convert string date from DB to datetime.date object for st.date_input
                    edited_start_date = st.date_input("Start Date", value=pd.to_datetime(project_to_edit['start_date']).date(), key="edit_project_start_date")
                    edited_end_date = st.date_input("End Date", value=pd.to_datetime(project_to_edit['end_date']).date(), key="edit_project_end_date")
                    edited_budget = st.number_input("Budget ($)", value=float(project_to_edit['budget']), min_value=0.0, format="%.2f", key="edit_project_budget")
                    submitted_edit = st.form_submit_button("Update Project") # REMOVED key="edit_project_submit"
                    if submitted_edit:
                        # Call your update_project function here
                        update_project(selected_project_id_from_df, edited_name, edited_description, edited_start_date, edited_end_date, edited_budget)
                        st.success("Project updated successfully!")
                        st.rerun()
            else:
                st.warning("Please select a project to edit.")

        elif project_action == "Delete Selected Project":
            # Section for deleting selected project
            if selected_project_id_from_df:
                project_name_to_delete = projects_df[projects_df['id'] == selected_project_id_from_df]['project_name'].iloc[0]
                st.error(f"Deleting Project: **{project_name_to_delete}**")
                # `st.button` is outside a form, so its `key` is fine if needed
                if st.button("Confirm Delete Project", type="secondary", key="confirm_delete_project_btn"): # This key is likely fine.
                    # Call your delete_project function here
                    delete_project(selected_project_id_from_df)
                    st.success("Project deleted successfully!")
                    st.rerun()
            else:
                st.warning("Please select a project to delete.")


    else: # If projects_df is empty, only show "Add New Project" form
        st.info("You don't have any projects yet. Use the form below to create one.")
        # This form is displayed directly as there are no existing projects to manage
        with st.form("add_project_form_if_empty"):
            project_name = st.text_input("Project Name (e.g., Road Resurfacing Phase A)", key="add_project_name_empty")
            description = st.text_area("Description", key="add_project_desc_empty")
            start_date = st.date_input("Start Date", value=datetime.today(), key="add_project_start_date_empty")
            end_date = st.date_input("End Date", value=datetime.today(), key="end_date_empty")
            budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f", key="budget_empty")
            submitted = st.form_submit_button("Add Project") # REMOVED key="add_project_submit_empty"
            if submitted:
                if add_project(st.session_state.user_id, project_name, description, start_date, end_date, budget):
                    st.success(f"Project '{project_name}' added!")
                    st.rerun()
                else:
                    st.error("Failed to add project. Please check input.")

        # If projects_df is empty, no CSV to download for projects
        # No project selection or edit/delete forms either, as there are no projects.

def tasks_page_content():
    if not st.session_state.selected_project_id:
        st.warning("No project selected. Please go to 'My Projects' tab and select one to manage tasks.")
        return # Exit early if no project selected

    st.subheader(f"Tasks for Project: {st.session_state.selected_project_name}")

    tasks_df = get_tasks_by_project(st.session_state.selected_project_id)

    selected_task_id_from_df = None # Initialize outside conditional blocks

    # Determine initial radio button selection for tasks based on flag
    initial_task_action_index = 0 # Default to "Add New Task"
    if st.session_state.show_add_task_form:
        initial_task_action_index = 0 # "Add New Task" is typically the first option
        st.session_state.show_add_task_form = False # CLEAR THE FLAG

    # Determine initial filter selection based on flag
    initial_filter_status_index = 0 # Default to 'All'
    if st.session_state.filter_tasks_status != 'All':
        # Find the index of the 'Overdue' option in the selectbox
        status_options = ['All', 'Overdue', 'Not Overdue'] # Ensure this matches your selectbox options
        if st.session_state.filter_tasks_status in status_options:
            initial_filter_status_index = status_options.index(st.session_state.filter_tasks_status)
        st.session_state.filter_tasks_status = 'All' # CLEAR THE FLAG after acting on it


    if not tasks_df.empty:
        st.write("### Current Tasks")
        # Apply conditional styling for overdue tasks
        def highlight_overdue(row):
            if row['Is Overdue']:
                return ['background-color: #ffcccc'] * len(row) # Light red background
            return [''] * len(row)

        st.dataframe(tasks_df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        overall_progress = tasks_df['progress_percentage'].mean() if not tasks_df.empty else 0
        st.metric(label="Overall Project Progress", value=f"{overall_progress:.1f}%")
        st.progress(overall_progress / 100.0)

        overdue_tasks_count = tasks_df[tasks_df['Is Overdue']].shape[0]
        if overdue_tasks_count > 0:
            st.warning(f"🚨 You have **{overdue_tasks_count}** overdue tasks in this project!")
            st.dataframe(tasks_df[tasks_df['Is Overdue']], use_container_width=True, hide_index=True) # Optionally show just overdue ones
        else:
            st.info("🎉 No overdue tasks for this project! Keep up the good work.")

        # --- Data Visualization: Tasks by Status ---
        st.markdown("---")
        st.write("### Task Status Distribution")
        status_counts = tasks_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_status = px.pie(status_counts, values='Count', names='Status',
                             title='Tasks by Status',
                             color_discrete_sequence=px.colors.sequential.RdBu) # Using a sequential color scale
        st.plotly_chart(fig_status, use_container_width=True)

        # --- Data Visualization: Tasks by Priority ---
        st.markdown("---")
        st.write("### Task Priority Distribution")
        priority_counts = tasks_df['task_priority'].value_counts().reset_index()
        priority_counts.columns = ['Priority', 'Count']
        fig_priority = px.bar(priority_counts, x='Priority', y='Count',
                             title='Tasks by Priority',
                             labels={'Priority': 'Task Priority', 'Count': 'Number of Tasks'},
                             color='Priority',
                             category_orders={"Priority": ["High", "Medium", "Low"]}, # Order for display
                             color_discrete_map={"High": "red", "Medium": "orange", "Low": "green"})
        st.plotly_chart(fig_priority, use_container_width=True)


        # --- Filtering/Sorting for Tasks ---
        st.markdown("---")
        st.write("### Filter and Sort Tasks")
        col_filter0, col_filter1, col_filter2, col_filter3 = st.columns(4)
        # Add a new filter option
        with col_filter0: # Or a new column
            filter_overdue = st.selectbox("Filter by Overdue", ['All', 'Overdue', 'Not Overdue'])
        with col_filter1:
            filter_status = st.selectbox("Filter by Status", ['All'] + tasks_df['status'].unique().tolist())
        with col_filter2:
            filter_assigned_to = st.selectbox("Filter by Assignee", ['All'] + tasks_df['assigned_to'].unique().tolist())
        with col_filter3:
            # Include 'task_priority' in sort options
            sort_by = st.selectbox("Sort by", ['Task No.', 'task_name', 'status', 'progress_percentage', 'due_date', 'task_priority'])
            sort_order = st.radio("Order", ['Ascending', 'Descending'], horizontal=True)

        
        if filter_overdue == 'Overdue':
            filtered_tasks_df = filtered_tasks_df[filtered_tasks_df['Is Overdue'] == True]
        elif filter_overdue == 'Not Overdue':
            filtered_tasks_df = filtered_tasks_df[filtered_tasks_df['Is Overdue'] == False]

        filtered_tasks_df = tasks_df.copy()
        if filter_status != 'All':
            filtered_tasks_df = filtered_tasks_df[filtered_tasks_df['status'] == filter_status]
        if filter_assigned_to != 'All':
            filtered_tasks_df = filtered_tasks_df[filtered_tasks_df['assigned_to'] == filter_assigned_to]

        if sort_order == 'Ascending':
            filtered_tasks_df = filtered_tasks_df.sort_values(by=sort_by, ascending=True)
        else:
            filtered_tasks_df = filtered_tasks_df.sort_values(by=sort_by, ascending=False)

        st.dataframe(filtered_tasks_df, use_container_width=True, hide_index=True)
        if filtered_tasks_df.empty and (filter_status != 'All' or filter_assigned_to != 'All'):
            st.info("No tasks match your filter criteria.")


        # --- Search Functionality for Tasks ---
        st.markdown("---")
        search_task_term = st.text_input("Search Tasks by Name/Assignee", key="task_search_bar")
        if search_task_term:
            # Apply search to already filtered df
            filtered_tasks_df = filtered_tasks_df[
                filtered_tasks_df['task_name'].str.contains(search_task_term, case=False, na=False) |
                filtered_tasks_df['assigned_to'].str.contains(search_task_term, case=False, na=False)
            ]
            st.dataframe(filtered_tasks_df, use_container_width=True, hide_index=True)
            if filtered_tasks_df.empty:
                st.info("No tasks match your search criteria.")


        # --- Export to CSV for Tasks ---
        csv_export_tasks = filtered_tasks_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Tasks as CSV",
            data=csv_export_tasks,
            file_name=f"tasks_data_{st.session_state.selected_project_name}.csv",
            mime="text/csv",
            key="download_tasks_csv"
        )

        st.write("### Select a Task to Edit or Delete")
        if not tasks_df.empty: # Make sure there are tasks to select from originally
            selected_task_id_from_df = st.selectbox(
                "Select Task",
                options=tasks_df['id'].tolist(), # Still select by database ID
                format_func=lambda x: f"T{tasks_df[tasks_df['id'] == x]['Task No.'].iloc[0]} - {tasks_df[tasks_df['id'] == x]['task_name'].iloc[0]}",
                key="select_task_to_manage"
            )
        else:
            selected_task_id_from_df = None
    else:
        st.info("No tasks added for this project yet.")
        selected_task_id_from_df = None

    st.markdown("---")
    st.write("### Add | Edit | Delete Tasks")
    task_action = st.radio("Choose task action", ("Add New Task", "Edit Selected Task", "Delete Selected Task"), horizontal=True)
    status_options = ['Not Started', 'In Progress', 'On Hold', 'Completed', 'Cancelled']
    priority_options = ['Low', 'Medium', 'High'] # Define priority options

    if task_action == "Add New Task":
        with st.form("add_task_form"):
            task_name = st.text_input("Task Name (e.g., Foundation Excavation)")
            status = st.selectbox("Status", options=status_options)
            # CORRECTED: Changed st.selectbox for priority
            task_priority = st.selectbox("Task Priority", options=priority_options, index=priority_options.index('Medium')) # Default to Medium
            progress_percentage = st.slider("Progress (%)", 0, 100, 0)
            assigned_to = st.text_input("Assigned To (Optional)")
            due_date = st.date_input("Due Date", value=datetime.today())
            submitted = st.form_submit_button("Add Task")
            if submitted:
                # CORRECTED: Pass task_priority to add_task
                if add_task(st.session_state.selected_project_id, task_name, status, task_priority, progress_percentage, assigned_to, due_date):
                    st.success(f"Task '{task_name}' added!")
                    st.rerun()

    elif task_action == "Edit Selected Task":
        # Check if a task is selected before trying to edit
        if selected_task_id_from_df:
            selected_task_data = tasks_df[tasks_df['id'] == selected_task_id_from_df].iloc[0]
            with st.form("edit_task_form"):
                st.write(f"Editing Task: **{selected_task_data['task_name']}**")
                edited_task_name = st.text_input("Task Name", value=selected_task_data['task_name'])
                edited_status = st.selectbox("Status", options=status_options, index=status_options.index(selected_task_data['status']))
                # CORRECTED: Added the edit input for task_priority
                edited_task_priority = st.selectbox("Task Priority", options=priority_options,
                                                     index=priority_options.index(selected_task_data['task_priority'] if pd.notna(selected_task_data['task_priority']) else 'Medium')) # Handle potential NaN/None
                edited_progress_percentage = st.slider("Progress (%)", 0, 100, int(selected_task_data['progress_percentage']))
                edited_assigned_to = st.text_input("Assigned To (Optional)", value=selected_task_data['assigned_to'] if pd.notna(selected_task_data['assigned_to']) else "")
                edited_due_date = st.date_input("Due Date", value=pd.to_datetime(selected_task_data['due_date']))
                submitted_edit = st.form_submit_button("Update Task")
                if submitted_edit:
                    # CORRECTED: Pass edited_task_priority to update_task
                    update_task(selected_task_id_from_df, edited_task_name, edited_status, edited_task_priority, edited_progress_percentage, edited_assigned_to, edited_due_date)
                    st.success("Task updated successfully!")
                    st.rerun()
        else:
            st.warning("Please select a task to edit.")

    elif task_action == "Delete Selected Task":
        # Check if a task is selected before trying to delete
        if selected_task_id_from_df:
            st.error(f"Deleting Task: **{tasks_df[tasks_df['id'] == selected_task_id_from_df]['task_name'].iloc[0]}**")
            if st.button("Confirm Delete Task", type="secondary"):
                delete_task(selected_task_id_from_df)
                st.success("Task deleted successfully!")
                st.rerun()
        else:
            st.warning("Please select a task to delete.")



def generate_project_report_html(project_id, user_id): # user_id currently unused, consider if needed
    conn = None
    try:
        conn = get_db_connection()
        # Fetch project data into a DataFrame first
        project_df = pd.read_sql_query("SELECT * FROM projects WHERE id = ?", conn, params=(project_id,))

        if project_df.empty:
            st.error(f"Error: Project with ID {project_id} not found.")
            return None # Or return an empty HTML string

        project_data = project_df.iloc[0] # Now it's safe to access iloc[0]
    except Exception as e:
        st.error(f"Database error while fetching project: {e}")
        return None
    finally:
        if conn:
            conn.close()

    tasks_df = get_tasks_by_project(project_id) # This function now includes 'Is Overdue'

    # Project Summary
    html_content = f"<h1>Project Report: {project_data['project_name']}</h1>"
    html_content += f"<p><strong>Description:</strong> {project_data['description']}</p>"
    html_content += f"<p><strong>Start Date:</strong> {project_data['start_date']}</p>"
    html_content += f"<p><strong>End Date:</strong> {project_data['end_date']}</p>"
    html_content += f"<p><strong>Budget:</strong> ${project_data['budget']:,.2f}</p>" # Corrected formatting

    html_content += "<h2>Task Overview</h2>"
    if not tasks_df.empty:
        overall_progress = tasks_df['progress_percentage'].mean()
        html_content += f"<p><strong>Overall Project Progress:</strong> {overall_progress:.1f}%</p>"
        html_content += f"<p><strong>Total Tasks:</strong> {len(tasks_df)}</p>"
        completed_tasks = tasks_df[tasks_df['status'] == 'Completed'].shape[0]
        html_content += f"<p><strong>Completed Tasks:</strong> {completed_tasks}</p>"
        overdue_tasks_count = tasks_df[tasks_df['Is Overdue']].shape[0] # Assumes 'Is Overdue' is boolean
        html_content += f"<p><strong>Overdue Tasks:</strong> <span style='color:red;'>{overdue_tasks_count}</span></p>"

        display_tasks_df = tasks_df[['Task No.', 'task_name', 'status', 'task_priority', 'progress_percentage', 'assigned_to', 'due_date', 'Is Overdue']].copy()
        display_tasks_df['due_date'] = display_tasks_df['due_date'].dt.strftime('%Y-%m-%d')

        # Convert 'Is Overdue' boolean to 'Yes'/'No' for display BEFORE to_html
        # This makes the string replacement more targeted and robust.
        display_tasks_df['Is Overdue'] = display_tasks_df['Is Overdue'].map({True: 'Yes', False: 'No'})

        styled_html_table = display_tasks_df.to_html(index=False, classes='tasks-table', escape=False)
        
        # Apply styling:
        # Style header
        styled_html_table = styled_html_table.replace('<th>Is Overdue</th>', '<th style="color:red;">Is Overdue</th>')
        # Style 'Yes' cells in 'Is Overdue' column
        # Now we replace based on the content 'Yes' which is more specific than 'True'
        styled_html_table = styled_html_table.replace('<td>Yes</td>', '<td style="color:red; font-weight:bold;">Yes</td>')
        # 'No' cells don't need specific styling beyond the default, but this ensures consistency if you wanted to style them too.
        # styled_html_table = styled_html_table.replace('<td>No</td>', '<td>No</td>') # This line is effectively a no-op if 'No' is already the string

        html_content += styled_html_table

        html_content += """
        <style>
            .tasks-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            .tasks-table th, .tasks-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .tasks-table th { background-color: #f2f2f2; }
            /* .overdue-task { background-color: #ffdddd; } */ /* Class defined but not used yet */
        </style>
        """

        # Add Visualizations
        html_content += "<h2>Visualizations</h2>"
        try:
            # Task Status Distribution
            status_counts = tasks_df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig_status = px.pie(status_counts, values='Count', names='Status',
                                title='Tasks by Status',
                                color_discrete_sequence=px.colors.sequential.RdBu)
            img_bytes_status = fig_status.to_image(format="png") # Requires kaleido
            encoded_img_status = base64.b64encode(img_bytes_status).decode('utf-8')
            html_content += f"<img src='data:image/png;base64,{encoded_img_status}' style='width: 100%; max-width: 600px; display: block; margin: 10px auto;'><br>"

            # Task Priority Distribution
            priority_counts = tasks_df['task_priority'].value_counts().reset_index()
            priority_counts.columns = ['Priority', 'Count']
            fig_priority = px.bar(priority_counts, x='Priority', y='Count',
                                title='Tasks by Priority',
                                labels={'Priority': 'Task Priority', 'Count': 'Number of Tasks'},
                                color='Priority',
                                category_orders={"Priority": ["High", "Medium", "Low"]},
                                color_discrete_map={"High": "red", "Medium": "orange", "Low": "green"})
            img_bytes_priority = fig_priority.to_image(format="png") # Requires kaleido
            encoded_img_priority = base64.b64encode(img_bytes_priority).decode('utf-8')
            html_content += f"<img src='data:image/png;base64,{encoded_img_priority}' style='width: 100%; max-width: 600px; display: block; margin: 10px auto;'><br>"
        except Exception as e:
            st.warning(f"Could not generate visualizations. Ensure 'kaleido' is installed (pip install kaleido). Error: {e}")
            html_content += "<p><em>Visualizations could not be generated.</em></p>"
    else:
        html_content += "<p>No tasks found for this project.</p>"

    return html_content


def generate_pdf_from_html(html_content, filename="report.pdf"): # filename not used by weasyprint here
    try:
        from weasyprint import HTML
        # You can also pass a CSS stylesheet to WeasyPrint if you have external CSS
        # from weasyprint import CSS
        # css = CSS(string=''' @page { size: A4; margin: 1in; } ''')
        # pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css])
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        st.error("WeasyPrint library not found. Please install it (`pip install weasyprint`) to generate PDFs.")
        st.info("You can still view the HTML preview below.")
        return None
    except Exception as e:
        st.error(f"Error generating PDF with WeasyPrint: {e}")
        return None


def reports_page_content():
    # Assume st.session_state.username and st.session_state.user_id are set
    if 'username' not in st.session_state: st.session_state.username = "TestUser"
    if 'user_id' not in st.session_state: st.session_state.user_id = 101


    st.subheader(f"Generate Project Reports, {st.session_state.username}")

    projects_df = get_projects_by_user(st.session_state.user_id)

    if projects_df.empty:
        st.info("You need to add projects first to generate reports. Go to 'My Projects' tab.")
        return

    # More robust way to map display names to IDs
    project_display_to_id_map = {
        f"P{row['User Project ID']} - {row['project_name']}": row['id']
        for _, row in projects_df.iterrows()
    }
    project_options = list(project_display_to_id_map.keys())

    selected_project_display = st.selectbox(
        "Select Project for Report",
        options=project_options,
        key="report_project_selector"
    )

    if selected_project_display:
        selected_project_id = project_display_to_id_map.get(selected_project_display)

        if selected_project_id is None:
            st.error("Error: Could not determine selected project ID.")
            return

        st.markdown("---")
        st.write(f"### Previewing Report for: {selected_project_display}")

        if st.button("Generate Report HTML & PDF", key="generate_report_btn"):
            with st.spinner("Generating report..."):
                report_html = generate_project_report_html(selected_project_id, st.session_state.user_id)

            if report_html:
                st.success("Report HTML generated!")

                st.markdown("#### HTML Preview:")
                # Use a container with a fixed height for better layout if preview is long
                with st.container():
                    st.components.v1.html(report_html, height=500, scrolling=True)

                pdf_bytes = generate_pdf_from_html(report_html) # filename is for download button
                if pdf_bytes:
                    report_file_name = f"Project_Report_{selected_project_display.replace(' ', '_').replace('-', '')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.download_button(
                        label="Download Project Report (PDF)",
                        data=pdf_bytes,
                        file_name=report_file_name,
                        mime="application/pdf",
                        key="download_pdf_report"
                    )
                else:
                    st.warning("PDF could not be generated. Check messages above if WeasyPrint is installed and for other errors.")
            else:
                st.error("Could not generate report HTML. Project might not exist or an error occurred.")

# --- Main App Logic ---
if not st.session_state.logged_in:
    login_register_section() # Show login/register if not logged in
else:
    # --- Top Navigation Tabs ---
    st.title("Civil Engineering Project Tracker") # Main title visible after login

    # User Info and Logout in a header/info bar
    # Using columns to place user info and logout button horizontally
    user_info_col, logout_col = st.columns([0.7, 0.3])
    with user_info_col:
        st.info(f"Welcome, **{st.session_state.username}**! You are logged in.")
    with logout_col:
        # Move logout button to top bar
        if st.button("Logout", key="top_logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.selected_project_id = None
            st.session_state.selected_project_name = None
            st.session_state.current_view = 'Dashboard' # Reset view on logout
            st.success("Logged out successfully.")
            st.rerun()

    st.markdown("---") # Separator below user info / logout

    # Custom Top Navigation Buttons
    nav_cols = st.columns(4) # One column for each main nav item
    with nav_cols[0]:
        # It's good practice to make these keys more descriptive, e.g., "nav_dashboard_button"
        if st.button("Dashboard", use_container_width=True, key="nav_dashboard_button", help="Click to go to Dashboard"):
            st.session_state.current_view = 'Dashboard'
            st.rerun()

    with nav_cols[1]:
        if st.button("My Projects", use_container_width=True, key="nav_projects_button", help="Click to manage your Projects"):
            st.session_state.current_view = 'Projects'
            st.rerun()

    with nav_cols[2]:
        if st.button("Tasks", use_container_width=True, key="nav_tasks_button", help="Click to manage Tasks for the selected Project"):
            st.session_state.current_view = 'Tasks'
            st.rerun()
            
    with nav_cols[3]:
        # CHANGE KEY AND LABEL HERE!
        if st.button("Reports", use_container_width=True, key="nav_reports_button", help="Click to generate Project Reports"): # <--- FIX IS HERE
            st.session_state.current_view = 'Reports'
            st.rerun()
    # NOTE: The above uses a common Streamlit trick for 'active tab' highlighting.
    # It renders a hidden st.button that actually triggers the state change,
    # and a visible st.markdown with a custom button-like div that applies styling.
    # The `onclick` JavaScript simulates a click on the hidden Streamlit button.
    # This is a workaround for Streamlit not having native 'active tab' styling for custom buttons.

    st.markdown("---") # Separator below navigation buttons

    # --- Page Routing based on current_view ---
    if st.session_state.current_view == 'Dashboard':
        dashboard_page_content()
    elif st.session_state.current_view == 'Projects':
        projects_page_content()
    elif st.session_state.current_view == 'Tasks':
        tasks_page_content()
    elif st.session_state.current_view == 'Reports': # NEW
        reports_page_content()
    # Add other pages here if you expand the navigation

    


    # --- Optional: Sidebar for Logo and Contact Info ---
    with st.sidebar:
        # --- Logo Placement ---
        # Assuming 'image_9b4949.jpg' is the correct image file for your logo
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
        # st.markdown("---")
        # st.markdown("Developed by: Yusuff Olatunji Sikiru")
        # st.markdown("Version 1.0")

# Adding a footer
footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed with ❤️ by <a style='display: inline; text-align: center;' href="https://bit.ly/atozaboutdata" target="_blank">Yusuff Olatunji Sikiru</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)