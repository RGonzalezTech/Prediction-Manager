# Prediction Manager

A mobile-first web application to track probability-weighted predictions ("bets") between two users.

## Running the Application

### Prerequisites

- Docker
- Docker Compose

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/prediction-manager.git
    cd prediction-manager
    ```

2.  **Run the application:**
    ```bash
    docker-compose up -d
    ```

3.  **Access the application:**
    Open your browser and navigate to `http://localhost:8000`.

## Development

### Backend

The backend is a FastAPI application. The main entry point is `app/main.py`.

### Frontend

The frontend is built with Jinja2 templates and TailwindCSS. The templates are located in `app/templates`.

### Database

The application uses a SQLite database. The database file is located in the `data` directory.