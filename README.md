# The-Issue-Is-Backend

This is the backend for the 'The-Issue-Is' project. This is a Python Flask application that uses MindsDB to generate high-quality GitHub issues. The API has been containerized using Docker.

## Run Locally

Clone the project

```bash
  git clone https://github.com/MinuraPunchihewa/the-issue-is-backend.git
```

Go to the project directory

```bash
  cd the-issue-is-backend
```

Build the Docker image

```bash
  docker build -t the-issue-is-backend .
```

Start the server

```bash
  docker run -p 8080:8080 the-issue-is-backend
```

