from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# from ..dependencies import auth
from ichrisbirch import schemas
from ichrisbirch.api import crud
from ichrisbirch.db.sqlalchemy.session import sqlalchemy_session

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get("/", response_model=list[schemas.Task])
async def read_many(
    db: Session = Depends(sqlalchemy_session), completed_filter: Optional[str] = None, limit: Optional[int] = None
):
    """API method to read many tasks.  Passes request to crud.tasks module"""
    print(f'{completed_filter=}')
    return crud.tasks.read_many(db, completed_filter=completed_filter, limit=limit)


@router.get("/completed/", response_model=list[schemas.TaskCompleted])
async def completed(
    db: Session = Depends(sqlalchemy_session),
    start_date: Union[str, None] = None,
    end_date: Union[str, None] = None,
    first: Union[bool, None] = None,
    last: Union[bool, None] = None,
):
    """API method to get completed tasks.  Passes request to crud.tasks module"""
    return crud.tasks.completed(
        db,
        start_date=start_date,
        end_date=end_date,
        first=first,
        last=last,
    )


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
    if not (task := crud.tasks.complete_task(task_id, db)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.get("/search/{search_terms}/", response_model=list[schemas.Task])
async def search(search_terms: str, db: Session = Depends(sqlalchemy_session)):
    """API method to search for tasks"""
    return crud.tasks.search(search_terms, db)
