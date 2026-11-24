from datetime import date #IMPORTACIONES DE LIBRERIAS NECESARIAS.

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

#CREACIÓN DE MODELOS DE BASE DE DATOS, CLASES QUE REPRESENTAN LAS TABLAS DE LA BASE DE DATOS.
class Base(DeclarativeBase):
    pass


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(unique=True)
    descripcion: Mapped[str]
    #RELACIÓN ENTRE CATEGORIAS Y EQUIPOS, UNA CATEGORIA PUEDE TENER MUCHOS EQUIPOS.
    equipos: Mapped[list["Equipo"]] = relationship(
        back_populates="categoria"
    )


class Equipo(Base):
    __tablename__ = "equipos"
    #CONSTRAINTS PARA VALIDAR QUE EL PRECIO DIARIO SEA MAYOR A 0, EL STOCK TOTAL Y DISPONIBLE NO SEA NEGATIVO Y QUE EL STOCK DISPONIBLE NO SEA MAYOR AL STOCK TOTAL.
    __table_args__ = (
        CheckConstraint("precio_diario > 0"),
        CheckConstraint("stock_total >= 0"),
        CheckConstraint("stock_disponible >= 0"),
        CheckConstraint("stock_disponible <= stock_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]
    tipo: Mapped[str] = mapped_column(server_default="general")
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id")
    )
    precio_diario: Mapped[float]
    stock_total: Mapped[int]
    stock_disponible: Mapped[int]

    categoria: Mapped["Categoria"] = relationship(
        back_populates="equipos"
    )
    arriendos: Mapped[list["Arriendo"]] = relationship(
        back_populates="equipo"
    )

    __mapper_args__ = {"polymorphic_on": tipo, "polymorphic_identity": "general"}


class EquipoProteccion(Equipo):
    __mapper_args__ = {"polymorphic_identity": "proteccion"}


class EquipoEntrenamiento(Equipo):
    __mapper_args__ = {"polymorphic_identity": "entrenamiento"}


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]
    correo: Mapped[str] = mapped_column(unique=True)
    telefono: Mapped[str]

    arriendos: Mapped[list["Arriendo"]] = relationship(
        back_populates="cliente"
    )


class Arriendo(Base):
    __tablename__ = "arriendos"

    __table_args__ = (
        CheckConstraint("cantidad > 0"),
        CheckConstraint("fecha_fin_prevista >= fecha_inicio"),
        CheckConstraint("estado IN ('ACTIVO', 'DEVUELTO')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipo_id: Mapped[int] = mapped_column(
        ForeignKey("equipos.id")
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id")
    )
    fecha_inicio: Mapped[date]
    fecha_fin_prevista: Mapped[date]
    cantidad: Mapped[int]
    estado: Mapped[str] = mapped_column(default="ACTIVO")

    equipo: Mapped["Equipo"] = relationship(
        back_populates="arriendos"
    )
    cliente: Mapped["Cliente"] = relationship(
        back_populates="arriendos"
    )
