from fastapi import FastAPI, Query
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

""" Sobre los modelos 

    1. En ningún caso se le asignó un tipo a las variables. 
    Si bien el ORM será capaz de generar las tablas correspondientes, al no indicar los tipos
    de las variables, la experiencia de desarrollo en estos modelos se degradará.

    2. En general, la práctica aceptada es que los nombres de tablas en bases de datos no estén en plural (cars, subsidiaries).
    Es por ello que las clases indicadas en el ejercicio no lo estan.
"""
class Car(Base):
    __tablename__ = 'cars' 
    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    model = Column(String)
    brand = Column(String)
    subsidiary_id = Column(Integer, ForeignKey('subsidiaries.id'))
    created_at = Column(DateTime, default=datetime.utcnow) # Desde la documentación: The method "utcnow" in class "datetime" is deprecated
    subsidiary = relationship("Subsidiary", back_populates="cars")

class Subsidiary(Base):
    __tablename__ = 'subsidiaries' # En general, la práctica aceptada es que los nombres de tablas en bases de datos no estén en plural. 
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    cars = relationship("Car", back_populates="subsidiary")

# Debido a que el servicio declarado en el archivo docker-compose.yml tiene como nombre 'base_de_datos', el hostname de postgres sería tambien 'base_de_datos'.
# base_de_datos://username:password@localhost:5432/asj'
engine = create_engine('postgresql://username:password@localhost:5432/asj') # Estos no son los datos reales de la base de datos segun se ha declarado en el compose. 

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

app = FastAPI()


""" Sobre los endpoints

    1. En ambos métodos no se declaró el tipo (type) de respuesta, por lo cual 
    la documentación autogenerada no tendrá efecto o será impresisa.

    2. Ambos métodos fueron declarados como async, sin emabargo, la configuración del ORM
    en este archivo no parece indicar ser una sesión asíncrona.  https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html.
    La keyword async no debe ser utilizada sin cuidado. 

    3. La conexión a la base de datos, db = SessionLocal(), no indica ser un singleton. 
    Es por ello que en cada request a estos endpoints generará una conexión independiente la db haciendo
    el proceso menos eficiente.

    4. La declaración de argumentos en el endpoint get_cars indican que son de tipo str. 
    Sin embargo, Query(None) indica que los argumentos pueden ser None.
    La declaración correcta, en python 3.10+ pudo haber sido 
        - brand: str | None
        - subsidiaryName: str | None 

    5. subsiadiaryName está en camelCase, sin embargo, en python se recomienda el uso de snake_case (subsidiary_name).

    6. En ningún endpoint se hace uso de pydantic. Precisamente, el endpoint create_car recibe un objeto (sqlalchemy.orm object) de tipo Car.
    El mismo no funcionará

    7. El retorno de create_car es un diccionario. Lo ideal hubiese sido implementar pydantic para ello. 
"""
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

# Utilizado de ésta manera, el comportamiento de db.close() de manera global puede ser errático.
# Dando como resultado cierres inesperados a la conexión con la db. 
db.close()
