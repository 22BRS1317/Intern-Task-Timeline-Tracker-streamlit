from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum
from datetime import datetime

Base = declarative_base()

class TaskStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    tasks = relationship("Task", back_populates="user")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    deadline = Column(DateTime, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="tasks")
    comments = relationship("Comment", back_populates="task")

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    task = relationship("Task", back_populates="comments")
    user = relationship("User")

# Database initialization
def init_db():
    engine = create_engine('sqlite:///intern_tracker.db')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

# Helper functions
def get_user_by_username(session, username):
    return session.query(User).filter(User.username == username).first()

def get_tasks_by_user(session, user_id):
    return session.query(Task).filter(Task.user_id == user_id).all()

def get_all_tasks(session):
    return session.query(Task).all()

def create_task(session, title, description, deadline, user_id):
    task = Task(
        title=title,
        description=description,
        deadline=deadline,
        user_id=user_id
    )
    session.add(task)
    session.commit()
    return task

def update_task_status(session, task_id, status):
    task = session.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = status
        session.commit()
    return task

def add_comment(session, content, task_id, user_id):
    comment = Comment(
        content=content,
        task_id=task_id,
        user_id=user_id
    )
    session.add(comment)
    session.commit()
    return comment 