import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database, schemas

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)