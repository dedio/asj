from fastapi import FastAPI, Query
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Car(Base):
    __tablename__ = 'cars'
    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    model = Column(String)
    brand = Column(String)
    subsidiary_id = Column(Integer, ForeignKey('subsidiaries.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    subsidiary = relationship("Subsidiary", back_populates="cars")

class Subsidiary(Base):
    __tablename__ = 'subsidiaries'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    cars = relationship("Car", back_populates="subsidiary")

engine = create_engine('postgresql://username:password@localhost:5432/asj')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

app = FastAPI()

@app.get("/cars")
async def get_cars(brand: str = Query(None), subsidiaryName: str = Query(None)):
    try:
        query = db.query(Car)
        if brand:
            query = query.filter(Car.brand == brand)
        if subsidiaryName:
            query = query.join(Subsidiary).filter(Subsidiary.name == subsidiaryName)
        cars = query.all()
        return cars
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener los datos")

@app.post("/cars")
async def create_car(car: Car):
    try:
        new_car = Car(
            year=car.year, 
            brand=car.brand, 
            model=car.model, 
            subsidiary_id=car.subsidiary_id            
        )
        db.add(new_car)
        db.commit()
        query_subsidiary = db.query(Subsidiary)
        subsidiary = query_subsidiary.filter(id = new_car.subsidiary_id)
        return {
            "id": new_car.id,
            "year": new_car.year,
            "brand": new_car.brand,
            "createdAt": new_car.created_at,
            "subsidiary_id": new_car.subsidiary_id,
            "subsidiary": {
                "id": subsidiary.id,
                "name": subsidiary.name,
                "createdAt": subsidiary.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al agregar el vehículo en la base de datos")

db.close()
