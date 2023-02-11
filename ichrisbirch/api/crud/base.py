from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ichrisbirch.db.sqlalchemy.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD"""

    def __init__(self, model: Type[ModelType]):
        """CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def read_one(self, id: Any, db: Session) -> Optional[ModelType]:
        """Default method for reading one row from db

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            id (Any): id of row to read

        Returns:
            Optional[ModelType]: row of db as a SQLAlchemy model
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def read_many(self, db: Session, *, skip: int = 0, limit: int = 5000) -> List[ModelType]:
        """Default method for reading many rows from db

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            skip (int, optional): Number of rows to skip. Defaults to 0.
            limit (int, optional): Limit number of returned rows. Defaults to 5000.

        Returns:
            List[ModelType]: List of rows as SQLAlchemy models
        """
        return db.query(self.model).order_by(self.model.id).offset(skip).limit(limit).all()

    def create(self, obj_in: CreateSchemaType, db: Session) -> ModelType:
        """Insert row in db from SQLAlchemy model

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            obj_in (Pydantic schema): Schema for creating a db row

        Returns:
            ModelType: SQLAlchemy model of the inserted row
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]], db: Session) -> ModelType:
        """Update db row

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            db_obj (SQLAlchemy Model): SQLAlchemy model to use for the update
            obj_in (Union[UpdateSchemaType, Dict[str, Any]]): Pydantic model or dict to insert

        Returns:
            ModelType: SQLAlchemy model of the updated row
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, id: int, db: Session) -> ModelType | None:
        """Delete row from db

        Args:
            db (SQLAlchemy Session): Session to use for transaction
            id (int): id of row to delete

        Returns:
            ModelType: SQLAlchemy model of the deleted row
            None: If the row does not exsit
        """
        if obj := db.query(self.model).filter(self.model.id == id).first():
            db.delete(obj)
            db.commit()
            return obj
        return None
