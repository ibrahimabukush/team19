# ISEND - Smart Academic Request Management System

ISEND is a smart web-based platform designed to improve how academic institutions handle student requests. Traditional systems often rely on manual processes, resulting in delays, lack of transparency, and frustration for both students and administrators.

ISEND solves this by offering a fully automated, AI-driven platform that allows students to submit requests easily, receive real-time status updates, and communicate directly with the institution via an integrated chatbot. Staff and administrators benefit from dashboards, data analysis tools, and intelligent notification systems.

---

## Project Summary

ISEND provides:

* A modern and secure digital system for managing academic requests
* A built-in AI-powered chatbot for guiding users
* Real-time status tracking for each submitted request
* Role-based dashboards for students, admins, and secretaries
* A robust backend built with Django and a clean, responsive frontend

This platform ensures smoother internal workflows, better service to students, and reduced processing times for staff.

---

## Key Features

* Easy online request submission
* AI chatbot integration
* Real-time dashboards and reports
* Status tracking and alerts
* Secure authentication system
* Admin approval and task assignment
* Automated email notifications
* Multilingual and accessibility-ready structure (planned)

---

## Technologies Used

* Python 3.10+
* Django Framework
* SQLite (for development)
* HTML5, CSS3, JavaScript
* Bootstrap 5
* Django Templates
* Git / GitHub

---

## Installation Guide

### Prerequisites

* Python 3.10 or newer
* pip (Python package manager)
* Git (optional)

### Step-by-Step Setup

1. **Clone the Project**

   ```bash
   git clone https://github.com/Ibrahimabukush/team19/ISEND.git
   cd ISEND
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   # For Linux/macOS:
   source venv/bin/activate
   # For Windows:
   venv\Scripts\activate
   ```

3. **Install Required Packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply Migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create Superuser**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the Server**

   ```bash
   python manage.py runserver
   ```

7. **Visit in Browser**

   ```
   http://127.0.0.1:8000/
   ```

---

## Testing the System

* Admin login: /admin
* Create student and secretary accounts
* Submit test requests
* Track status
* Use chatbot for assistance

---

## Project Structure

```
ISEND/
├── blog/             # Chatbot and core features
├── users/            # Custom user logic
├── static/           # CSS, JS, images
├── templates/        # HTML templates
├── db.sqlite3        # Development database
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
```

---

## Future Feature Suggestions

* Multilingual support (e.g., Arabic, Hebrew, English)
* Integration with cloud services (Google Drive, Office365)
* Personalized suggestions using AI
* Two-factor authentication and secure API key management
* Mobile app version
* Detailed request analytics and export tools
* LMS integration
* Student portal for progress tracking
* Smart alerts for staff

---

## Developers

This project was developed as part of the Project Management Course at Shamoon College of Engineering (SCE).

**Team 19 – ISEND Platform:**

* Maysa Abu Shareb
* Ibrahim Abu Kosh
* Yazed Alasd
* Ahmad Alddah

---

## Contact

For more information, please contact the development team via GitHub or your academic institution.

© 2025 – All rights reserved.
