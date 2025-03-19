# Real-Time Chat Application

A modern, real-time chat application built with Django, Django Channels, and WebSockets.

## Features

- **Real-time messaging**: Instant message delivery using WebSockets
- **User authentication**: Secure login and registration
- **Message management**: Users can edit and delete their own messages
- **Message search**: Search functionality within conversations
- **Responsive design**: Works on desktop and mobile devices
- **RESTful API**: Comprehensive API for message operations
- **Pagination**: Efficient loading of messages with pagination

## Technology Stack

- **Backend**: Django 3.2+
- **Real-time communication**: Django Channels 3.0+
- **WebSockets**: ASGI with Daphne
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **API**: Django REST Framework
- **Authentication**: Django Authentication System

## API Endpoints

### Messages API

- `GET /api/messages/`: Retrieve messages (paginated, 10 per page)
  - Query parameters:
    - `user`: Filter by username
    - `page`: Page number
    - `page_size`: Number of messages per page (max 100)
- `POST /api/messages/`: Create a new message
- `GET /api/messages/{id}/`: Retrieve a specific message
- `POST /api/messages/{id}/update_message/`: Update a message
- `DELETE /api/messages/{id}/delete_message/`: Delete a message

## Installation

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chat-application.git
   cd chat-application
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Access the application at http://127.0.0.1:8000/

## Testing

The application includes comprehensive tests for models, views, and API endpoints. To run the tests:

```bash
python manage.py test
```

To generate a test coverage report:

```bash
coverage run --source=chat manage.py test
coverage report
```

## Creating Dummy Data

You can populate the database with dummy data for testing:

```bash
python manage.py create_dummy_data --users 15 --messages 300
```

This will create 15 test users and 300 random messages between them.

## Project Structure

```
chat-application/
├── chat/                   # Main application
│   ├── management/         # Custom management commands
│   ├── migrations/         # Database migrations
│   ├── models.py           # Data models
│   ├── serializers.py      # API serializers
│   ├── consumers.py        # WebSocket consumers
│   ├── views.py            # Views and API endpoints
│   └── tests.py            # Test suite
├── templates/              # HTML templates
│   └── chat.html           # Main chat interface
├── static/                 # Static files (CSS, JS)
├── manage.py               # Django management script
└── README.md               # This file
```

## Code Documentation

The codebase is thoroughly documented with docstrings following the Google Python Style Guide. Key components include:

- **Models**: Data structure and relationships
- **Views**: HTTP request handling and template rendering
- **Consumers**: WebSocket connection handling
- **Serializers**: Data validation and transformation
- **Tests**: Comprehensive test coverage

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Django and Django Channels communities
- Bootstrap for the responsive design
- All contributors to the project
