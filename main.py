import datetime

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from google.genai.types import GenerateContentConfig
from sqlalchemy.orm import Session
from app import models, database, schemas
from google import genai


app = FastAPI(title="Harmonia API")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Health check: success."}


@app.post("/users/login", response_model=schemas.UserBase)
def find_or_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if db_user:
        return db_user

    new_user = models.User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/habits/{habit_id}/toggle", response_model=schemas.Habit)
def toggle_habit_completion(habit_id: int, db: Session = Depends(get_db)):
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not db_habit:
        raise HTTPException(status_code=404, detail="Hábito não encontrado")

    db_habit.is_completed = not db_habit.is_completed
    db.commit()
    db.refresh(db_habit)
    return db_habit


@app.post("/coach/ask")
def ask_coach(question: models.CoachQuestion):

    system_prompt = [
        "Você é o 'Harmonia', um coach de saúde e bem-estar amigável e motivacional. ",
        "Seu objetivo é fornecer conselhos práticos, seguros e positivos baseados em princípios de saúde. ",
        "Nunca dê conselhos médicos diretos ou diagnósticos. Sempre incentive o usuário a consultar um profissional de saúde para questões sérias. ",
        "Responda de forma concisa e encorajadora."
    ]

    client = genai.Client()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=question.text, config=GenerateContentConfig(
            system_instruction=system_prompt
        ))
        return {"answer": response.text}
    except Exception as e:
        print(f"erro: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao processar sua pergunta.")


@app.get("/dashboard/user/{user_id}", response_model=schemas.DashboardDataResponse)
def get_dashboard_data(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Busca os hábitos do usuário para a data de hoje
    today = datetime.date.today()
    print(today)
    db_habits = db.query(models.Habit).filter(
        models.Habit.user_id == user_id,
        models.Habit.date == today
    ).all()

    dashboard_data = schemas.DashboardDataResponse(
        userName=db_user.name.split(" ")[0],
        activity=schemas.ActivityData(steps=7890),
        sleep=schemas.SleepData(duration="5h42min"),
        dailyInsight="Notei que nos dias em que você atinge sua meta de passos, seu sono profundo melhora em 15%.",
        habits=db_habits
    )

    return dashboard_data


@app.get("/users/{user_id}", response_model=schemas.User)
def get_user_details(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_user


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)