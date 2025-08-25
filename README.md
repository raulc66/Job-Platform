# Job Board Project

This is a Django-based job board application that allows users to browse job listings, apply for jobs, and manage their accounts. The project is structured to facilitate development and deployment, with separate configurations for development and production environments.

## Project Structure

```
jobboard/
├── manage.py               # Command-line utility for managing the Django project
├── requirements.txt        # Python packages required for the project
├── README.md               # Documentation for the project
├── .gitignore              # Files and directories to be ignored by Git
├── .env.example            # Template for environment variables
├── media/                  # Directory for user-uploaded files (development)
├── static_cdn/             # Directory for collected static files (production/local)
├── jobboard/               # Main Django project package
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   ├── settings/           # Configuration settings for the project
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── templates/          # HTML templates for rendering views
│   │   ├── base.html
│   │   └── includes/       # Optional partial templates
│   │       ├── navbar.html
│   │       └── footer.html
│   └── static/             # Static files (CSS, JS, images)
│       ├── css/
│       ├── js/
│       └── img/
├── apps/                   # Individual Django applications
│   ├── accounts/           # User accounts and authentication
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── signals.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── templates/accounts/
│   │       ├── login.html
│   │       └── signup.html
│   ├── companies/          # Company-related functionality
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── jobs/               # Job-related functionality
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── templates/jobs/
│   │       ├── job_list.html
│   │       ├── job_detail.html
│   │       └── job_form.html
│   └── applications/       # Job applications
│       ├── __init__.py
│       ├── apps.py
│       ├── admin.py
│       ├── models.py
├── test_smoke.py           # Smoke tests for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd jobboard
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in the necessary values.

5. **Run migrations:**
   ```
   python manage.py migrate
   ```

6. **Run the development server:**
   ```
   python manage.py runserver
   ```

## Usage

- Navigate to `http://127.0.0.1:8000/` to access the job board application.
- Users can register, log in, and apply for jobs.
- Admins can manage job listings and user accounts through the Django admin interface.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.