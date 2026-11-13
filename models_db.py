from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

BASE = Path(__file__).resolve().parent
(BASE / "data").mkdir(exist_ok=True)

Base = declarative_base()
engine = create_engine(f"sqlite:///{BASE / 'data' / 'pqrs.db'}")
Session = sessionmaker(bind=engine)

class Solicitante(Base):
    __tablename__ = "solicitantes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(120))
    correo = Column(String(200), nullable=False)
    acepta_datos = Column(Boolean, default=False)

class Pqrs(Base):
    __tablename__ = "pqrs"
    id = Column(Integer, primary_key=True)
    radicado = Column(String(20), unique=True)
    solicitante_id = Column(Integer, ForeignKey("solicitantes.id"))
    fecha_radicacion = Column(DateTime, default=datetime.now)
    canal = Column(String(30), default="web")
    entidad = Column(String(100))
    ciudad = Column(String(60))
    regimen = Column(String(30))
    tipo = Column(String(30))
    tema = Column(String(60))
    texto = Column(Text, nullable=False)
    urgencia_predicha = Column(String(10))
    prob_urgencia = Column(Float)
    estado = Column(String(20), default="radicada")
    correo_enviado = Column(Boolean, default=False)
    solicitante = relationship("Solicitante")

Base.metadata.create_all(engine)