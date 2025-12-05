Technical Specification: Prediction Manager

1. Executive Summary

Project Name: Prediction Manager
Objective: Develop a mobile-first web application hosted on a local network to track probability-weighted predictions ("bets") between two specific users (e.g., Husband and Wife).
Core Mechanic: The application calculates "payout odds" based on the confidence level of the prediction. High confidence = Low Payout / High Risk.

2. Infrastructure & Deployment

The application is designed as a lightweight monolith to run on a Raspberry Pi via Docker.

Architecture: Single Container (Monolith).

OS/Environment: Linux (Raspberry Pi / ARM64 compatible).

Containerization: Docker & Docker Compose.

Network: Local Home Network (Port 8000).

Security:

Auth: None (Public Trust Model).

User Identity: Select user via UI dropdown.

Persistence: SQLite database file stored in a mounted Docker volume.

3. Technology Stack

Backend: Python 3.11+ using FastAPI.

Database: SQLite.

ORM: SQLAlchemy (Async preferred) or Tortoise-ORM.

Frontend: HTML5 templates served by Jinja2, styled with TailwindCSS (via CDN for simplicity).

Runtime: uvicorn server.

4. Database Schema

4.1. users

Represents the two participants.

id: Integer (PK)

name: String (Seeded with "Husband", "Wife")

4.2. categories

Groups predictions for filtering.

id: Integer (PK)

name: String (e.g., "Love is Blind", "General", "Politics")

4.3. predictions

The core betting entity.

id: Integer (PK)

description: String (The content of the bet)

creator_id: Integer (FK -> users.id)

category_id: Integer (FK -> categories.id)

confidence: Float (0.50 to 0.99)

status: String/Enum (OPEN, RESOLVED, REDEEMED)

outcome: Boolean (Nullable. TRUE = Creator was right, FALSE = Creator was wrong)

created_at: DateTime

5. Business Logic: The "Odds" Algorithm

The payout is determined by the confidence ($P$) set by the creator.
The "Unit" is an abstract currency (e.g., 1 Unit = $1.00 or 1 Chore).

Formula

$$\text{Odds Ratio (R)} = \frac{P}{1 - P}$$

Scenario A: Creator Wins

If the prediction comes true:

Creator receives 1 Unit from the Opponent.

Scenario B: Creator Loses

If the prediction does not come true:

Creator pays R Units to the Opponent.

Examples

Confidence

Odds Ratio (Payout)

Explanation

50%

1.0 : 1

Even money. Risk 1 to win 1.

66%

2.0 : 1

Creator is confident. Risks 2 to win 1.

80%

4.0 : 1

Creator is very confident. Risks 4 to win 1.

95%

19.0 : 1

"Sure thing". Risks 19 to win 1.

6. API Endpoints (REST)

Frontend Routes

GET /: Dashboard. Renders active bets and current debt stats.

GET /new: Form to create a new prediction.

JSON API Routes

GET /api/stats: Returns the net "debt" between users calculated from all RESOLVED (but not REDEEMED) predictions.

POST /api/predictions: Create a new prediction.

Payload: { "creator_id": 1, "description": "...", "confidence": 0.8, "category_id": 1 }

POST /api/predictions/{id}/resolve: Mark prediction as correct/incorrect.

Payload: { "outcome": true } (or false)

POST /api/predictions/{id}/redeem: Mark a debt as paid/settled. Status moves from RESOLVED to REDEEMED.

7. UI/UX Requirements (Mobile First)

Design Philosophy: Function over form, large touch targets, "Thumb-friendly".

7.1. Dashboard

Scoreboard: Prominently display who owes whom. (e.g., "Karina owes You: 4.5 Units").

Active List: List of unresolved predictions.

Display: Description, Confidence %, Potential Payout.

Floating Action Button (FAB): Large + button to add a prediction.

7.2. Creation Screen

Who is betting? Toggle/Dropdown (User A / User B).

Confidence Slider:

Range: 50% - 99%.

Dynamic Feedback: As the slider moves, show the calculation: "You are risking 4.0 units to win 1.0 unit."

7.3. Resolution

Simple "Yes/No" buttons on active cards to resolve them.

Once resolved, the loser sees a "Mark Paid" button to clear the debt from the scoreboard.

8. Development Setup Guide

Repository Init: Initialize a new Git repo.

Docker Setup:

Create Dockerfile based on python:3.11-slim.

Create docker-compose.yml mapping port 8000:8000 and volume ./data:/app/data.

Dependency Management: Use requirements.txt listing fastapi, uvicorn, sqlalchemy, jinja2.

Database Migration: On app startup, check if prediction.db exists. If not, create tables and seed default Users/Categories.

9. Deliverables

Source code repository.

docker-compose.yml file.

Instructions on how to run on Raspberry Pi (e.g., docker compose up -d).