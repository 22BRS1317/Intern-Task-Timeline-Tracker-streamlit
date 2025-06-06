import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import bcrypt
from database import (
    init_db, User, Task, Comment, TaskStatus,
    get_user_by_username, get_tasks_by_user, get_all_tasks,
    create_task, update_task_status, add_comment
)
from utils import format_timedelta, send_email_notification, check_overdue_tasks, send_task_assignment_notification, send_task_completion_notification, send_task_update_notification

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'show_create_task' not in st.session_state:
    st.session_state.show_create_task = False

# Initialize database
Session = init_db()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def register_user(username, password, email, is_admin=False):
    """Register a new user."""
    if get_user_by_username(Session, username):
        return False, "Username already exists"
    
    hashed_password = hash_password(password)
    new_user = User(
        username=username,
        password=hashed_password,
        email=email,
        is_admin=is_admin
    )
    Session.add(new_user)
    Session.commit()
    return True, "Registration successful"

def login(username, password):
    user = get_user_by_username(Session, username)
    if user and verify_password(password, user.password):
        st.session_state.authenticated = True
        st.session_state.user = user
        return True
    return False

def create_timeline_plot(tasks):
    if not tasks:
        return go.Figure()  # Return empty figure if no tasks
        
    df = pd.DataFrame([
        {
            'Task': task.title,
            'Start': task.created_at,
            'End': task.deadline,
            'Status': task.status.value,
            'Description': task.description
        }
        for task in tasks
    ])
    
    # Create a Gantt chart using plotly.graph_objects
    fig = go.Figure()
    
    for status in TaskStatus:
        status_tasks = df[df['Status'] == status.value]
        if not status_tasks.empty:
            fig.add_trace(go.Bar(
                x=[(row['End'] - row['Start']).total_seconds() * 1000 for _, row in status_tasks.iterrows()],
                y=status_tasks['Task'],
                base=[row['Start'] for _, row in status_tasks.iterrows()],
                orientation='h',
                name=status.value,
                text=status_tasks['Description'],
                hovertemplate='<b>%{y}</b><br>' +
                            'Start: %{base|%Y-%m-%d}<br>' +
                            'End: %{x|%Y-%m-%d}<br>' +
                            'Description: %{text}<extra></extra>'
            ))
    
    fig.update_layout(
        title="Task Timeline",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=400,
        barmode='stack',
        showlegend=True
    )
    
    return fig

def create_status_chart(tasks):
    if not tasks:
        return go.Figure()  # Return empty figure if no tasks
        
    status_counts = pd.DataFrame([
        {'Status': status.value, 'Count': len([t for t in tasks if t.status == status])}
        for status in TaskStatus
    ])
    
    fig = px.pie(status_counts, values='Count', names='Status',
                 title='Task Status Distribution',
                 color='Status',
                 color_discrete_map={
                     'not_started': 'gray',
                     'in_progress': 'yellow',
                     'completed': 'green',
                     'overdue': 'red'
                 })
    return fig

def create_new_task(title, description, deadline, assigned_user_id):
    """Create a new task and assign it to a user."""
    try:
        task = create_task(Session, title, description, deadline, assigned_user_id)
        # Send task assignment notification
        assigned_user = Session.query(User).filter(User.id == assigned_user_id).first()
        send_task_assignment_notification(task, assigned_user)
        return True, "Task created successfully"
    except Exception as e:
        return False, f"Error creating task: {str(e)}"

def update_task_status(session, task_id, new_status):
    """Update task status and send notification."""
    task = session.query(Task).filter(Task.id == task_id).first()
    if task:
        old_status = task.status
        task.status = new_status
        session.commit()
        
        # Send appropriate notifications
        if new_status == TaskStatus.COMPLETED:
            send_task_completion_notification(task, task.user)
        elif old_status != new_status:
            send_task_update_notification(task, task.user, new_status)
    return task

def main():
    st.set_page_config(page_title="Intern Task Timeline Tracker", layout="wide")
    
    if not st.session_state.authenticated:
        st.title("Intern Task Timeline Tracker")
        
        # Toggle between login and register
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                st.session_state.show_register = False
        with col2:
            if st.button("Register", use_container_width=True):
                st.session_state.show_register = True
        
        if not st.session_state.show_register:
            # Login Form
            st.subheader("Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if login(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        else:
            # Registration Form
            st.subheader("Register")
            with st.form("register_form"):
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                email = st.text_input("Email")
                is_admin = st.checkbox("Register as Admin")
                submit = st.form_submit_button("Register")
                
                if submit:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        success, message = register_user(new_username, new_password, email, is_admin)
                        if success:
                            st.success(message)
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(message)
    else:
        st.sidebar.title(f"Welcome, {st.session_state.user.username}")
        
        # Admin controls in sidebar
        if st.session_state.user.is_admin:
            st.sidebar.subheader("Admin Controls")
            if st.sidebar.button("Create New Task"):
                st.session_state.show_create_task = True
            
            if st.session_state.show_create_task:
                with st.sidebar.form("create_task_form"):
                    st.subheader("Create New Task")
                    task_title = st.text_input("Task Title")
                    task_description = st.text_area("Task Description")
                    task_deadline = st.date_input("Deadline")
                    task_time = st.time_input("Deadline Time")
                    
                    # Get all users for assignment
                    all_users = Session.query(User).filter(User.is_admin == False).all()
                    user_options = {user.username: user.id for user in all_users}
                    selected_username = st.selectbox(
                        "Assign to",
                        options=list(user_options.keys())
                    )
                    
                    if st.form_submit_button("Create Task"):
                        if task_title and task_description:
                            deadline = datetime.combine(task_deadline, task_time)
                            success, message = create_new_task(
                                task_title,
                                task_description,
                                deadline,
                                user_options[selected_username]
                            )
                            if success:
                                st.success(message)
                                st.session_state.show_create_task = False
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.error("Please fill in all required fields")
        
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
        
        # Main content
        st.title("Intern Task Timeline Tracker")
        
        # Get tasks based on user role
        if st.session_state.user.is_admin:
            tasks = get_all_tasks(Session)
        else:
            tasks = get_tasks_by_user(Session, st.session_state.user.id)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Timeline", "Tasks", "Analytics"])
        
        with tab1:
            st.plotly_chart(create_timeline_plot(tasks), use_container_width=True)
        
        with tab2:
            # Add task filters
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All"] + [status.value for status in TaskStatus]
                )
            with col2:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Deadline", "Status", "Title"]
                )
            
            # Filter and sort tasks
            filtered_tasks = tasks
            if status_filter != "All":
                filtered_tasks = [t for t in filtered_tasks if t.status.value == status_filter]
            
            if sort_by == "Deadline":
                filtered_tasks.sort(key=lambda x: x.deadline)
            elif sort_by == "Status":
                filtered_tasks.sort(key=lambda x: x.status.value)
            else:  # Title
                filtered_tasks.sort(key=lambda x: x.title)
            
            for task in filtered_tasks:
                with st.expander(f"{task.title} - {task.status.value}"):
                    st.write(f"**Description:** {task.description}")
                    st.write(f"**Deadline:** {task.deadline.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Assigned to:** {task.user.username}")
                    
                    # Status update with completion time tracking
                    new_status = st.selectbox(
                        "Update Status",
                        [status.value for status in TaskStatus],
                        key=f"status_{task.id}"
                    )
                    
                    if st.button("Update", key=f"update_{task.id}"):
                        if new_status == TaskStatus.COMPLETED.value:
                            # Record completion time
                            completion_time = datetime.now()
                            time_diff = completion_time - task.deadline
                            if time_diff.total_seconds() > 0:
                                st.warning(f"Task completed {format_timedelta(time_diff)} after deadline")
                            else:
                                st.success(f"Task completed {format_timedelta(abs(time_diff))} before deadline")
                        
                        update_task_status(Session, task.id, TaskStatus(new_status))
                        st.rerun()
                    
                    # Comments section
                    st.subheader("Comments")
                    for comment in task.comments:
                        st.write(f"**{comment.user.username}** ({comment.created_at.strftime('%Y-%m-%d %H:%M')}):")
                        st.write(comment.content)
                    
                    new_comment = st.text_area("Add Comment", key=f"comment_{task.id}")
                    if st.button("Post Comment", key=f"post_{task.id}"):
                        if new_comment:
                            add_comment(Session, new_comment, task.id, st.session_state.user.id)
                            st.rerun()
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_status_chart(tasks), use_container_width=True)
            
            with col2:
                # Task completion rate
                completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
                total = len(tasks)
                completion_rate = (completed / total * 100) if total > 0 else 0
                
                st.metric("Task Completion Rate", f"{completion_rate:.1f}%")
                
                # Overdue tasks
                overdue = len([t for t in tasks if t.status == TaskStatus.OVERDUE])
                st.metric("Overdue Tasks", overdue)
                
                # On-time completion rate
                on_time_completed = len([
                    t for t in tasks 
                    if t.status == TaskStatus.COMPLETED and t.deadline >= datetime.now()
                ])
                on_time_rate = (on_time_completed / completed * 100) if completed > 0 else 0
                st.metric("On-time Completion Rate", f"{on_time_rate:.1f}%")

if __name__ == "__main__":
    main() 