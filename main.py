import uvicorn
from fastapi import FastAPI, Depends, HTTPException
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


@app.post("/test_users/", response_model=schemas.User, status_code=201)
def create_test_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.UserTest(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/test_users/", response_model=list[schemas.User])
def read_test_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.UserTest).offset(skip).limit(limit).all()
    return users


@app.post("/users/login", response_model=schemas.User)
def find_or_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if db_user:
        return db_user

    new_user = models.UserTest(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/coach/ask")
def ask_coach(question: models.CoachQuestion):
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=question.text
    )
    print(response.text)
    return response.text


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)