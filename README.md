# Intern Task Timeline Tracker

A web application built with Streamlit to help track and manage intern tasks, deadlines, and progress.

## Features

- User authentication (Admin and Regular users)
- Task creation and assignment
- Task status tracking
- Timeline visualization
- Analytics dashboard
- Email notifications
- Comments system

## Setup

1. Clone the repository:
```bash
git clone https://github.com/22BRS1317/Intern-Task-Timeline-Tracker.git
cd Intern-Task-Timeline-Tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Register a new account (first user will be admin)
2. Log in with your credentials
3. Create and manage tasks
4. Track progress through the timeline and analytics

## Technologies Used

- Python
- Streamlit
- SQLAlchemy
- Plotly
- SQLite
- SMTP for email notifications

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 