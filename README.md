# Multi-Agent E-commerce Chat API

This project is a multi-agent e-commerce chat API built with FastAPI, Google's ADK, and a Gemini model. It provides a conversational interface for an e-commerce platform, allowing users to interact with various agents to perform tasks such as searching for products, managing their cart, and viewing their order history.

## Project Overview

The goal of this project is to create a robust and intelligent e-commerce chat API that leverages the power of multiple specialized AI agents. Each agent is responsible for a specific domain, such as authentication, product search, or order management. The agents are orchestrated by a central agent that delegates tasks based on the user's request.

### Key Features

*   **Multi-Agent Architecture:** The system uses a collection of specialized agents to handle different tasks, making the system more modular and extensible.
*   **Conversational Interface:** Users can interact with the API in a natural, conversational way.
*   **Authentication:** The API provides a secure authentication system with JWT tokens.
*   **E-commerce Functionality:** The API supports essential e-commerce features, including product search, cart management, and order history.
*   **FastAPI:** The API is built with FastAPI, a modern, high-performance web framework for Python.
*   **Google's ADK:** The agents are built with Google's ADK, which provides a framework for building and running AI agents.
*   **Gemini Model:** The agents use a Gemini model to understand and respond to user requests.

## Architecture

The application is built around a multi-agent architecture, with a central orchestrator agent that delegates tasks to specialized agents. The API is built with FastAPI, and the agents are built with Google's ADK.

*   **FastAPI:** The API is built with FastAPI, which provides a modern, high-performance web framework for Python.
*   **Google's ADK:** The agents are built with Google's ADK, which provides a framework for building and running AI agents.
*   **Multi-Agent System:** The system uses a collection of specialized agents to handle different tasks, making the system more modular and extensible.
*   **Orchestrator Agent:** The orchestrator agent is responsible for receiving user requests and delegating them to the appropriate specialized agent.
*   **Specialized Agents:** The specialized agents are responsible for handling specific tasks, such as authentication, product search, and order management.
*   **Database:** The application uses a database to store data, such as users, products, and orders. The application is designed to work with SQLite, PostgreSQL, and MySQL.

## Getting Started

To get started with the project, you will need to have Python 3.7+ installed. You will also need to have a Google API key with the Gemini API enabled.

### Prerequisites

*   Python 3.7+
*   Google API key with the Gemini API enabled
*   `pip` for installing packages

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/your-username/multi-agent-ecommerce-chat-api.git
    cd multi-agent-ecommerce-chat-api
    ```

2.  Create a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

### Database Setup

The application uses a database to store data. By default, it is configured to use SQLite, but you can also use PostgreSQL or MySQL.

*   **SQLite:** No additional setup is required. The database will be created automatically when you run the application.
*   **PostgreSQL/MySQL:** You will need to create a database and user, and then update the `.env` file with the connection details.

### Running the Application

1.  Create a `.env` file by copying the `.env.example` file:

    ```bash
    cp .env.example .env
    ```

2.  Open the `.env` file and update the following variables:

    *   `GOOGLE_API_KEY`: Your Google API key
    *   `JWT_SECRET`: A secret key for signing JWT tokens
    *   `DATABASE_URL`: The connection string for your database (if you are not using SQLite)

3.  Run the application:

    ```bash
    uvicorn main:app --reload
    ```

The application will be available at `http://localhost:8000`.

## Configuration

The application is configured using environment variables. You can find a list of all the available options in the `.env.example` file.

| Variable             | Description                                                                                             | Default     |
| -------------------- | ------------------------------------------------------------------------------------------------------- | ----------- |
| `DB_TYPE`            | The type of database to use (`sqlite`, `postgresql`, `mysql`)                                           | `sqlite`    |
| `DB_NAME`            | The name of the database                                                                                | `ecommerce.db` |
| `DB_USER`            | The username for the database                                                                           | ``          |
| `DB_PASSWORD`        | The password for the database                                                                           | ``          |
| `DB_HOST`            | The host of the database                                                                                | ``          |
| `DB_PORT`            | The port of the database                                                                                | ``          |
| `DATABASE_URL`       | The connection string for the database (will be constructed if empty)                                   | ``          |
| `GOOGLE_API_KEY`     | Your Google API key                                                                                     | ``          |
| `JWT_SECRET`         | A secret key for signing JWT tokens                                                                     | ``          |
| `JWT_EXPIRATION_HOURS` | The number of hours until a JWT token expires                                                         | `24`        |

## API Endpoints

The API is documented with Swagger UI, which is available at `/docs`.

### Authentication

*   **`POST /api/auth/register`**: Register a new user.
*   **`POST /api/auth/token`**: Authenticate a user and get a JWT token.
*   **`GET /api/auth/verify`**: Verify a JWT token.

### Chat

*   **`POST /api/chat`**: Send a message to the chat API.

#### Example Request

```bash
curl -X POST "http://localhost:8000/api/chat" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <your-jwt-token>" \
-d '{
  "message": "I want to see all black T-shirts"
}'
```

## Agents

The application uses a multi-agent system to handle different tasks.

*   **Orchestrator Agent:** The main agent that receives user requests and delegates them to the appropriate specialized agent.
*   **Auth Agent:** Handles user authentication and registration.
*   **Schema Agent:** Responsible for initializing the database schema and inserting sample data.
*   **Product Agent:** Responsible for searching for products.
*   **Cart Agent:** Responsible for managing the user's shopping cart.
*   **Order Agent:** Responsible for managing user orders.
*   **User Agent:** Responsible for managing user data.

## Tools

The agents use a collection of tools to interact with the database and other services.

*   **`search_products(search_term)`:** Searches for products in the database.
*   **`get_user_cart(user_id)`:** Gets the contents of a user's shopping cart.
*   **`get_user_orders(user_id)`:** Gets a user's order history.
*   **`register_user(username, password, email, role)`:** Registers a new user.
*   **`authenticate_user(username, password)`:** Authenticates a user.
*   **`verify_jwt_token(token)`:** Verifies a JWT token.
*   **`create_database_schema()`:** Creates the database schema.
*   **`insert_sample_data()`:** Inserts sample data into the database.
