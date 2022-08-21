from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import auth
from ...common.schemas.tasks import TaskCreate, TaskSchema

from datetime import datetime
from ...api import crud
from sqlalchemy.orm import Session
from ...common.db.sqlalchemy import sqlalchemy_session

router = APIRouter(prefix='/tasks', tags=['tasks'])

# ----- CRUD ----- #


# WORKING
@router.get("/", response_model=List[TaskSchema])
async def read_many(db: Session = Depends(sqlalchemy_session), skip: int = 0, limit: int = 5000):
    return crud.tasks.read_many(db, skip=skip, limit=limit)


# WORKING
@router.get("/completed/", response_model=List[TaskSchema] | TaskSchema)
async def completed(
    db: Session = Depends(sqlalchemy_session),
    start_date: str = None,
    end_date: str = None,
    first: bool = None,
    last: bool = None,
):
    return crud.tasks.completed(
        db, start_date=start_date, end_date=end_date, first=first, last=last
    )


# WORKING
@router.post("/", response_model=TaskSchema)
async def create(db: Session = Depends(sqlalchemy_session), task: TaskCreate = None):
    return crud.tasks.create(db, obj_in=task)


# WORKING
@router.get("/{task_id}/", response_model=TaskSchema)
async def read_one(db: Session = Depends(sqlalchemy_session), task_id: int = None):
    if not (task := crud.tasks.read_one(db, id=task_id)):
        raise HTTPException(status_code=404, detail=f"TaskSchema {task_id} not found")
    return task


# Not using, keep for reference
# @router.post("/{task_id}/", response_model=TaskSchema)
# async def update(db: Session = Depends(sqlalchemy_session), task: TaskSchema = None):
#     return crud.tasks.update(db, obj_in=task)

# WORKING
@router.delete("/{task_id}/", status_code=204)
async def delete(db: Session = Depends(sqlalchemy_session), task_id: int = None):
    return crud.tasks.delete(db, id=task_id)


# WORKING
@router.post("/complete/{task_id}/", response_model=TaskSchema)
async def complete(db: Session = Depends(sqlalchemy_session), task_id: int = None):
    return crud.tasks.complete_task(db, id=task_id)
