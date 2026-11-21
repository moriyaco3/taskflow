from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg
import os


class TaskCreate(BaseModel):
    title: str
    completed: bool = False


app = FastAPI()

def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5433")),
        dbname=os.getenv("DB_NAME", "taskflow"),
        user=os.getenv("DB_USER", "taskflow"),
        password=os.environ["DB_PASSWORD"]
    )


@app.get("/")
def home():
    return {"message": "Welcome to TaskFlow!"}


@app.get("/tasks")
def get_tasks():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, title, completed FROM tasks")
            rows = cursor.fetchall()

    return [
        {"id": row[0], "title": row[1], "completed": row[2]}
        for row in rows
    ]



@app.post("/tasks")
def create_task(task: TaskCreate):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, completed)
                VALUES (%s, %s)
                RETURNING id, title, completed
                """,
                (task.title, task.completed)
            )
            row = cursor.fetchone()

    return {
        "id": row[0],
        "title": row[1],
        "completed": row[2]
    }


@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: TaskCreate):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET title = %s, completed = %s
                WHERE id = %s
                RETURNING id, title, completed
                """,
                (
                    updated_task.title,
                    updated_task.completed,
                    task_id
                )
            )
            row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "completed": row[2]
    }



@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id
                """,
                (task_id,)
            )
            row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {"message": "Task deleted successfully"}