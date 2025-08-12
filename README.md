# Pydantic AI Backend

### Summary

This is a Pydantic AI Backend application providing a foundation for building robust and scalable AI-powered services. This application can be used as a starting point for developing various types of AI systems, including chatbots and virtual assistants.

Key features:

- Database integration with SQLAlchemy
- Database migrations with Alembic
- JWT-based authentication and authorization
- Command-line interface for managing the application
- Proper logging and error handling
- API documentation with Swagger UI
- Docker support for easy deployment

Technologies used:

- FastAPI
- PydanticAI
- SQLAlchemy
- Alembic
- Docker

### Project Structure

```
pydantic-ai-agent/
  ├── README.md
  ├── alembic.ini
  ├── app.py
  ├── cli.py
  ├── docker-compose.yml
  ├── docker-entrypoint.sh
  ├── Dockerfile
  ├── requirements.txt
  ├── .dockerignore
  ├── .env.example
  ├── configs/
  │   ├── __init__.py
  │   ├── database.py
  │   └── logger.py
  ├── migrations/
  │   ├── README
  │   ├── env.py
  │   ├── script.py.mako
  │   ├── back_versions/
  │   │   └── 2a177df657c9_modify_schema_definitions_for_multi_.py
  │   └── versions/
  │       ├── 4eafa02ca717_chatmessage_model_update_human_and_ai_.py
  │       ├── 68901a9ce043_break_down_chatmessage_model_into_.py
  │       ├── 903b71052dad_modify_schema_definitions_for_multi_.py
  │       └── bfdbeedc66d5_json_fields_removed_from_chatmessage_.py
  └── src/
      ├── exception_handlers.py
      ├── helpers.py
      ├── models.py
      ├── ai_agent/
      │   ├── __init__.py
      │   ├── core.py
      │   ├── models.py
      │   ├── schemas.py
      │   ├── tools.py
      │   ├── utils.py
      │   └── routes/
      │       ├── chat.py
      │       └── chat_operation.py
      └── auth/
          ├── __init__.py
          ├── dependencies.py
          ├── exceptions.py
          ├── models.py
          ├── routes.py
          ├── schemas.py
          └── utils.py
```

### Project Setup:

- Create python virtual environment & activate it.
- Install the requirements from requirements.txt by running `pip install -r requirements.txt`.
- Create a .env file from `example.env` and fill up the variables.
- You can select the database of your choice. By default, the application is configured to use SQLite. If you want to use MysQL set `DB_TYPE` to `mysql` and fill up the MYSQL variables.
- Run the application by running `uvicorn app:app --host 0.0.0.0 --port 8001 --reload`. The application server will be running on port 8001 & watch for any changes. Change to your desired port if needed.
- Visit `http://localhost:8001` to verify if the application server has started successfully.
- You can now start building your application on top of this base application.

API Documentation Endpoints(Avaliable only in debug mode):

- `/docs`: Swagger UI documentation for the API endpoints.
- `/redoc`: ReDoc documentation for the API endpoints.

### Database Setup

The application is configured to use SQLite by default. To use a different database, such as MySQL or PostgreSQL, you will need to update the following environment variables in the `.env` file:

- `DB_TYPE`: Set to `mysql` or `postgresql`.
- `DB_HOST`: The hostname or IP address of the database server.
- `DB_PORT`: The port number of the database server.
- `DB_NAME`: The name of the database.
- `DB_USER`: The username for connecting to the database.
- `DB_PASS`: The password for connecting to the database.

After configuring the database connection, you will need to run the database migrations to create the necessary tables. You can do this by running the following command:

```bash
alembic upgrade head
```

### CLI Commands

The following cli commands are available:

- `python cli.py`:
  - `generate_key`: Generates a new secret key.
  - `create_superuser`: Creates a new superuser with the provided information.

### Deployment

The application can be deployed using Docker. To build the Docker image, run the following command:

```bash
docker build -t chatbot_backend .
```

To run the Docker container, run the following command:

```bash
docker-compose up -d
```

Or you can build and run the Docker container in a single command:

```bash
docker-compose up -d --build
```

This will start the application in a detached mode. You can then access the application at `http://localhost:8001` or the port you specified by DOCKER_PORT in the .env file.

To stop the Docker container, run the following command:

```bash
docker-compose down
```

To view the logs of the running container, run the following command:

```bash
docker-compose logs -f
```

To run the database migrations inside the Docker container, you can use the following command:

```bash
docker-compose exec chatbot_backend alembic upgrade head
```

To run the CLI commands inside the Docker container, you can use the following command:

```bash
docker-compose exec chatbot_backend python cli.py <command>
```

To browse files inside the Docker container, you can use the following command:

```bash
docker-compose exec chatbot_backend bash
```
