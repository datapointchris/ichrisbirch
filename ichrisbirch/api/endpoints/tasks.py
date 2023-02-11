from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# from ..dependencies import auth
from ichrisbirch import schemas
from ichrisbirch.api import crud
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get("/", response_model=list[schemas.Task])
async def read_many(db: Session = Depends(sqlalchemy_session), skip: int = 0, limit: int = 5000):
    """API method to read many tasks.  Passes request to crud.tasks module"""
    return crud.tasks.read_many(db, skip=skip, limit=limit)


@router.get("/completed/", response_model=Union[list[schemas.Task], list])
async def completed(
    db: Session = Depends(sqlalchemy_session),
    start_date: Union[str, None] = None,
    end_date: Union[str, None] = None,
    first: Union[bool, None] = None,
    last: Union[bool, None] = None,
) -> Union[list[schemas.Task], list]:
    """API method to get completed tasks.  Passes request to crud.tasks module"""
    if not (
        completed := crud.tasks.completed(
            db,
            start_date=start_date,
            end_date=end_date,
            first=first,
            last=last,
        )
    ):
        return []
    return completed


@router.post("/", response_model=schemas.Task)
async def create(task: schemas.TaskCreate, db: Session = Depends(sqlalchemy_session)):
    """API method to create a new task.  Passes request to crud.tasks module"""
    return crud.tasks.create(task, db)


@router.get("/{task_id}/", response_model=schemas.Task)
async def read_one(task_id: int, db: Session = Depends(sqlalchemy_session)):
    """API method to read one task.  Passes request to crud.tasks module"""
    if not (task := crud.tasks.read_one(task_id, db)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# Not using, keep for reference
# @router.post("/{task_id}/", response_model=schemas.Task)
# async def update(task: schemas.Task, db: Session = Depends(sqlalchemy_session)):
#     return crud.tasks.update(db, obj_in=task)


@router.delete("/{task_id}/", status_code=200)
async def delete(task_id: int, db: Session = Depends(sqlalchemy_session)):
    """API method to delete a task.  Passes request to crud.tasks module"""
    if not (task := crud.tasks.delete(task_id, db)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/complete/{task_id}/", response_model=schemas.Task)
async def complete(task_id: int, db: Session = Depends(sqlalchemy_session)):
    """API method to complete a task.  Passes request to crud.tasks module"""
    if not (task := crud.tasks.complete_task(db, id=task_id)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
