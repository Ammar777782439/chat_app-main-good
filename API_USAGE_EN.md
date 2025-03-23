# API Usage Guide

## Authentication

There are three ways to authenticate with the API:

### 1. Obtain a Token Using Username and Password (API)

You can obtain an authentication token directly by sending your username (or email) and password to the following endpoint:

```
POST /api/auth/login/
```

Example request data:

**For regular users**:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**For Google OAuth users**:
```json
{
  "username": "your_username",
  "password": "",
  "oauth": "true"
}
```

You can also use email instead of username in both cases.

Example using curl for regular users:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"your_username","password":"your_password"}' http://127.0.0.1:8000/api/auth/login/
```

Example using curl for Google OAuth users:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"your_username","password":"","oauth":"true"}' http://127.0.0.1:8000/api/auth/login/
```

Successful response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### 2. Token Authentication

An authentication token is automatically created when a new user account is created. To get your token:

1. Log in to the application through the user interface
2. Visit: `http://127.0.0.1:8000/api/token/` to get your authentication token
3. Use this token in all API requests by adding an HTTP header:
   ```
   Authorization: Token your_token_here
   ```

Example using curl:
```bash
curl -H "Authorization: Token your_token_here" http://127.0.0.1:8000/api/messages/
```

### 3. Session Authentication

1. Log in to the application through the user interface
2. Use the cookies created for authentication
3. Make sure to send cookies with each API request

Example using curl:
```bash
curl -b cookies.txt -c cookies.txt http://127.0.0.1:8000/api/messages/
```

## Message Endpoints

### Get Messages

```
GET /api/messages/
```

Query parameters:
- `user`: Filter messages by username
- `page`: Page number (default: 1)
- `page_size`: Number of messages per page (default: 10, max: 100)

Example:
```
GET /api/messages/?user=john&page=1&page_size=20
```

### Send a New Message

```
POST /api/messages/
```

Required data:
```json
{
  "receiver": "user_id",
  "content": "Message content"
}
```

### Update a Message

```
POST /api/messages/{id}/update_message/
```

Required data:
```json
{
  "content": "New message content"
}
```

### Delete a Message

```
DELETE /api/messages/{id}/delete_message/
```

## WebSocket API for Real-Time Messages

The application provides a WebSocket interface for real-time communication. You can use WebSockets to receive new messages, message updates, and deletion notifications as they happen.

### Connecting to WebSocket

Connection address:
```
ws://your-domain.com/ws/chat/{username}/
```
where `{username}` is the username of the user you want to chat with.

### Sending a New Message

To send a new message via WebSocket, send JSON in the following format:

```json
{
  "message": "Message content"
}
```

### Updating an Existing Message

To update an existing message, send JSON in the following format:

```json
{
  "message_id": 123,
  "message": "New message content"
}
```

### Deleting a Message

To delete a message, send JSON in the following format:

```json
{
  "delete_message_id": 123
}
```

### Receiving Events

You will receive events from the WebSocket in the following formats:

**New message:**
```json
{
  "sender": "username1",
  "receiver": "username2",
  "message": "Message content",
  "id": 123
}
```

**Message update:**
```json
{
  "sender": "username1",
  "receiver": "username2",
  "message": "Updated message content",
  "message_id": 123
}
```

**Message deletion:**
```json
{
  "sender": "username1",
  "receiver": "username2",
  "deleted_message_id": 123
}
```

## Important Notes

1. You must be authenticated to use any of the endpoints mentioned above.
2. You can only update or delete messages that you sent.
3. When using session authentication, make sure to send a CSRF token with POST/PUT/DELETE requests.
4. Authentication tokens are automatically created when a new user account is created.
5. WebSockets are used for real-time communication, while the REST API is used for asynchronous operations.
