import datetime
import json
from typing import List

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from google.genai.types import GenerateContentConfig
from sqlalchemy.orm import Session, joinedload
from app import models, database, schemas
from google import genai

from app.schemas import HabitSuggestion, SuggestionRequest

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


@app.post("/users/login", response_model=schemas.User)
def find_or_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.User)
        .options(joinedload(models.User.habits))
        .filter(models.User.email == user.email)
        .first()
    )

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
def ask_coach(request: schemas.CoachRequest):
    system_prompt = [
        "Você é o 'Harmonia', um coach de saúde e bem-estar amigável e motivacional. ",
        "Seu objetivo é fornecer conselhos práticos, seguros e positivos baseados em princípios de saúde. ",
        "Nunca dê conselhos médicos diretos ou diagnósticos. Sempre incentive o usuário a consultar um profissional de saúde para questões sérias. ",
        "Responda de forma concisa e encorajadora.",
    ]

    conversation_history = []
    for message in request.history:
        role = "user" if message.role == "user" else "model"
        conversation_history.append(
            {"role": role, "parts": [{"text": message.content}]}
        )

    client = genai.Client()

    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=GenerateContentConfig(system_instruction=system_prompt),
            history=conversation_history,
        )
        response = chat.send_message(
            message=request.current_message,
        )
        return {"answer": response.text}
    except Exception as e:
        print(f"erro: {e}")
        raise HTTPException(
            status_code=500, detail="Ocorreu um erro ao processar sua pergunta."
        )


@app.get("/dashboard/user/{user_id}", response_model=schemas.DashboardDataResponse)
def get_dashboard_data(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    today = datetime.date.today()
    print(today)
    db_habits = (
        db.query(models.Habit)
        .filter(models.Habit.user_id == user_id, models.Habit.date == today)
        .all()
    )

    dashboard_data = schemas.DashboardDataResponse(
        userName=db_user.name.split(" ")[0],
        activity=schemas.ActivityData(steps=7890),
        sleep=schemas.SleepData(duration="5h42min"),
        dailyInsight="Notei que nos dias em que você atinge sua meta de passos, seu sono profundo melhora em 15%.",
        habits=db_habits,
    )

    return dashboard_data


@app.post("/users/{user_id}/habits", response_model=schemas.Habit)
def create_habit_for_user(
    user_id: int, habit: schemas.HabitCreate, db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db_habit = models.Habit(
        name=habit.name,
        icon=habit.icon,
        date=datetime.date.today(),
        is_completed=False,
        user_id=user_id,
    )

    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit


@app.get("/users/{user_id}", response_model=schemas.User)
def get_user_details(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_user


@app.patch("/users/{user_id}", response_model=schemas.User)
def update_user_goal(
    user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db_user.main_goal = user_update.main_goal
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/onboarding/suggest-habits", response_model=List[HabitSuggestion])
def suggest_habits(request: SuggestionRequest):
    system_prompt = [
        "Você é o 'Harmonia', um coach de saúde e bem-estar amigável e motivacional. ",
        "Seu objetivo é fornecer conselhos práticos, seguros e positivos baseados em princípios de saúde. ",
        "Nunca dê conselhos médicos diretos ou diagnósticos. Sempre incentive o usuário a consultar um profissional de saúde para questões sérias. ",
        "Responda de forma concisa e encorajadora.",
    ]

    prompt = f"""
    Sugira 3 hábitos simples e eficazes para alguém cujo principal objetivo de saúde é '{request.objective}'.
    Para cada hábito, sugira também um ícone do 'SF Symbols' da Apple.
    Retorne a resposta como um array JSON válido, sem nenhum texto antes nem depois, como no seguinte formato:
    [
        {{"name": "Nome do Hábito 1", "icon": "icone.do.sf.symbol"}},
        {{"name": "Nome do Hábito 2", "icon": "outro.icone"}},
        {{"name": "Nome do Hábito 3", "icon": "mais.um.icone"}}
    ]
    """
    try:
        client = genai.Client()
        response = client.models.generate_content(
            config=GenerateContentConfig(
                system_instruction=system_prompt, response_mime_type="application/json"
            ),
            model="gemini-2.5-flash",
            contents=prompt,
        )
        suggested_habits = json.loads(response.text)
        return suggested_habits
    except Exception as e:
        print(f"Erro ao sugerir hábitos: {e}")
        raise HTTPException(
            status_code=500, detail="Não foi possível gerar sugestões de hábitos."
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
