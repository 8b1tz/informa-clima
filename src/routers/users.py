from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src import models, schemas, services, utils
from src.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register/", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = services.create_user(db, user)
    return db_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = services.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/upload-identity-photo/")
async def upload_identity_photo(
    token: str = Depends(oauth2_scheme),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    file_location = f"identity_photos/{user.id}_{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    user.identity_photo = file_location
    db.commit()
    db.refresh(user)

    return {"info": "Identity photo uploaded successfully"}

@router.post("/donation-location/", response_model=schemas.DonationLocation)
async def create_donation_location(
    location: schemas.DonationLocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_collector:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
    db_location = services.create_donation_location(db, location, current_user.id)
    return db_location

@router.delete("/donation-location/{location_id}", response_model=schemas.DonationLocationDeleteResponse)
async def delete_donation_location(
    location_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        response = services.delete_donation_location(db, location_id, current_user)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this location")
    return response


@router.put("/donation-location/{location_id}", response_model=schemas.DonationLocation)
async def update_donation_location(
    location_id: int,
    location_update: schemas.DonationLocationUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        db_location = services.update_donation_location(db, location_id, location_update, current_user)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this location")
    return db_location


@router.get("/donation-locations/", response_model=List[schemas.DonationLocation])
async def list_donation_locations(db: Session = Depends(get_db)):
    return services.list_donation_locations(db)


@router.get("/donation-locations/state/{state}", response_model=List[schemas.DonationLocation])
async def list_donation_locations_by_state(state: str, db: Session = Depends(get_db)):
    return services.list_donation_locations_by_state(db, state)
