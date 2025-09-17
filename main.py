import io
import json
from typing import List
import datetime
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from google.genai.types import GenerateContentConfig, UploadFileConfig
from sqlalchemy.orm import Session
from app import models, database, schemas
from google import genai
from datetime import date, time

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
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if db_user:
        return db_user

    new_user = models.User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/habits/{habit_def_id}/toggle", response_model=schemas.HabitStatus)
def toggle_habit_completion(
    habit_def_id: int, date_str: str, db: Session = Depends(get_db)
):
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD."
        )

    habit_def = (
        db.query(models.HabitDefinition)
        .filter(models.HabitDefinition.id == habit_def_id)
        .first()
    )
    if not habit_def:
        raise HTTPException(
            status_code=404, detail="Definição de hábito não encontrada"
        )

    completion = (
        db.query(models.HabitCompletion)
        .filter(
            models.HabitCompletion.habit_id == habit_def_id,
            models.HabitCompletion.date == target_date,
        )
        .first()
    )

    if completion:
        db.delete(completion)
        is_completed_now = False
    else:
        new_completion = models.HabitCompletion(habit_id=habit_def_id, date=target_date)
        db.add(new_completion)
        is_completed_now = True

    db.commit()

    return schemas.HabitStatus(
        id=habit_def.id,
        user_id=habit_def.user_id,
        name=habit_def.name,
        icon=habit_def.icon,
        is_completed=is_completed_now,
    )


@app.get("/habits/{habit_def_id}/history", response_model=schemas.HabitHistory)
def get_habit_history(habit_def_id: int, db: Session = Depends(get_db)):
    completions_query = (
        db.query(models.HabitCompletion)
        .filter(models.HabitCompletion.habit_id == habit_def_id)
        .order_by(models.HabitCompletion.date.desc())
        .all()
    )

    completed_dates = {completion.date for completion in completions_query}

    if not completed_dates:
        return schemas.HabitHistory(current_streak=0, completed_dates=[])

    current_streak = 0
    today = datetime.date.today()
    check_date = today

    if check_date not in completed_dates:
        check_date = today - datetime.timedelta(days=1)

    while check_date in completed_dates:
        current_streak += 1
        check_date -= datetime.timedelta(days=1)

    return schemas.HabitHistory(
        current_streak=current_streak,
        completed_dates=sorted(list(completed_dates), reverse=True),
    )


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
def get_dashboard_data(user_id: int, date_str: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD."
        )
    habit_definitions = (
        db.query(models.HabitDefinition)
        .filter(models.HabitDefinition.user_id == user_id)
        .all()
    )

    completed_today_ids = {
        c.habit_id
        for c in db.query(models.HabitCompletion)
        .filter(
            models.HabitCompletion.date == target_date,
            models.HabitCompletion.definition.has(user_id=user_id),
        )
        .all()
    }

    habits_status = [
        schemas.HabitStatus(
            id=definition.id,
            user_id=definition.user_id,
            name=definition.name,
            icon=definition.icon,
            is_completed=(definition.id in completed_today_ids),
        )
        for definition in habit_definitions
    ]

    return schemas.DashboardDataResponse(
        userName=db_user.name.split(" ")[0],
        activity=schemas.ActivityData(steps=7890),
        sleep=schemas.SleepData(duration="5h42min"),
        dailyInsight="Continue assim! A consistência é a chave para o sucesso.",
        habits=habits_status,
    )


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


@app.post("/users/{user_id}/journal", response_model=schemas.JournalEntry)
def create_or_update_journal_entry(
    user_id: int, entry: schemas.JournalEntryCreate, db: Session = Depends(get_db)
):
    db_entry = (
        db.query(models.JournalEntry)
        .filter(
            models.JournalEntry.user_id == user_id,
            models.JournalEntry.date == entry.date,
        )
        .first()
    )

    if db_entry:
        db_entry.mood = entry.mood.value
        db_entry.content = entry.content
    else:
        db_entry = models.JournalEntry(
            user_id=user_id,
            date=entry.date,
            mood=entry.mood.value,
            content=entry.content,
        )
        db.add(db_entry)

    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.get("/journal_entries/{user_id}", response_model=list[schemas.JournalEntry])
def get_journal_entries(user_id: int, db: Session = Depends(get_db)):
    entries = (
        db.query(models.JournalEntry)
        .filter(models.JournalEntry.user_id == user_id)
        .order_by(models.JournalEntry.date.desc())
        .all()
    )
    if not entries:
        return []
    return entries


@app.post("/activities/", response_model=schemas.Activity)
def create_activity(activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    activity_data = activity.model_dump()
    activity_data["activity_type"] = activity.activity_type.value
    db_activity = models.ActivityLog(**activity_data)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


@app.get("/users/{user_id}/activities/", response_model=list[schemas.Activity])
def read_user_activities(user_id: int, db: Session = Depends(get_db)):
    activities = (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.owner_id == user_id)
        .order_by(models.ActivityLog.date.desc())
        .all()
    )
    if not activities:
        return []
    return activities


@app.post("/users/{user_id}/habits", response_model=schemas.HabitDefinition)
def create_habit_definition(
    user_id: int, habit: schemas.HabitDefinitionCreate, db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db_habit_def = models.HabitDefinition(**habit.model_dump(), user_id=user_id)
    db.add(db_habit_def)
    db.commit()
    db.refresh(db_habit_def)
    return db_habit_def


@app.post("/nutrition/analyze-meal", response_model=schemas.NutritionAnalysisResponse)
async def analyze_meal_image(image: UploadFile = File(...)):
    image_bytes = await image.read()

    prompt = """
    Analise a imagem de comida. Por favor, identifique cada item alimentar e estime a quantidade.
    Para cada item, forneça uma estimativa de calorias, proteínas, carboidratos e gorduras.
    Além disso, forneça um insight geral sobre a refeição (ex: "Refeição balanceada, rica em proteínas" 
    ou "Pode ser alta em gorduras saturadas, considere uma porção menor na próxima vez.").

    Retorne a resposta como um JSON válido no seguinte formato, sem nenhum texto antes ou depois:
    {
        "foods": [
            {"food_name": "Nome do Alimento 1", "calories": 100, "protein": 10, "carbs": 15, "fat": 5},
            {"food_name": "Nome do Alimento 2", "calories": 250, "protein": 5, "carbs": 30, "fat": 12}
        ],
        "insights": "Sua análise geral aqui...",
        "total_calories": 350
    }
    """

    try:
        client = genai.Client()
        in_memory_file = io.BytesIO(image_bytes)

        temp_file_name = f"temp_{image.filename}"

        uploaded_file = client.files.upload(
            file=in_memory_file,
            config=UploadFileConfig(
                display_name=temp_file_name, mime_type="image/jpeg"
            ),
        )

        print(f"Arquivo enviado com sucesso: {uploaded_file.name}")

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[uploaded_file, prompt],
            config=GenerateContentConfig(response_mime_type="application/json"),
        )
        client.files.delete(name=uploaded_file.name)
        print(f"Arquivo temporário deletado: {uploaded_file.name}")

        analysis_data = json.loads(response.text)

        return analysis_data

    except Exception as e:
        print(f"Erro detalhado ao chamar a API do Gemini: {e}")
        raise HTTPException(
            status_code=500, detail="Ocorreu um erro ao processar a imagem com a IA."
        )


@app.post("/nutrition", response_model=schemas.NutritionLog)
def create_nutrition_log(
    log_data: schemas.NutritionLogCreate, db: Session = Depends(get_db)
):
    db_log = models.NutritionLog(
        user_id=log_data.user_id,
        log_date=log_data.log_date,
        total_calories=log_data.total_calories,
        total_protein=log_data.total_protein,
        total_carbs=log_data.total_carbs,
        total_fat=log_data.total_fat,
        insights=log_data.insights,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    for item_data in log_data.items:
        db_item = models.FoodItem(**item_data.dict(), nutrition_log_id=db_log.id)
        db.add(db_item)

    db.commit()
    db.refresh(db_log)
    return db_log


@app.post("/users/{user_id}/water", response_model=schemas.WaterLog)
def create_water_log_for_user(
    user_id: int, water_log: schemas.WaterLogCreate, db: Session = Depends(get_db)
):
    db_water_log = models.WaterLog(**water_log.dict(), user_id=user_id)
    db.add(db_water_log)
    db.commit()
    db.refresh(db_water_log)
    return db_water_log


@app.get("/users/{user_id}/water", response_model=List[schemas.WaterLog])
def read_water_logs_for_user(
    user_id: int, log_date: date = None, db: Session = Depends(get_db)
):
    if log_date is None:
        log_date = date.today()

    start_of_day = datetime.datetime.combine(log_date, time.min)
    end_of_day = datetime.datetime.combine(log_date, time.max)

    return (
        db.query(models.WaterLog)
        .filter(
            models.WaterLog.user_id == user_id,
            models.WaterLog.log_date >= start_of_day,
            models.WaterLog.log_date <= end_of_day,
        )
        .order_by(models.WaterLog.log_date.desc())
        .all()
    )


@app.delete("/water/{log_id}", status_code=204)
def delete_water_log(log_id: int, db: Session = Depends(get_db)):
    db_log = db.query(models.WaterLog).filter(models.WaterLog.id == log_id).first()
    if db_log is None:
        raise HTTPException(status_code=404, detail="Registro de água não encontrado")

    db.delete(db_log)
    db.commit()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
