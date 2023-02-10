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


@router.get("/completed/", response_model=list[schemas.Task] | schemas.Task | list)
async def completed(
    db: Session = Depends(sqlalchemy_session),
    start_date: str = None,
    end_date: str = None,
    first: bool = None,
    last: bool = None,
) -> list[schemas.Task] | list:
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
    else:
        return completed


@router.post("/", response_model=schemas.Task)
async def create(db: Session = Depends(sqlalchemy_session), task: schemas.TaskCreate = None):
    """API method to create a new task.  Passes request to crud.tasks module"""
    return crud.tasks.create(db, obj_in=task)


@router.get("/{task_id}/", response_model=schemas.Task)
async def read_one(db: Session = Depends(sqlalchemy_session), task_id: int = None):
    """API method to read one task.  Passes request to crud.tasks module"""
    if not (task := crud.tasks.read_one(db, id=task_id)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# Not using, keep for reference
# @router.post("/{task_id}/", response_model=schemas.Task)
# async def update(db: Session = Depends(sqlalchemy_session), task: schemas.Task = None):
#     return crud.tasks.update(db, obj_in=task)


@router.delete("/{task_id}/", status_code=200)
async def delete(db: Session = Depends(sqlalchemy_session), task_id: int = None):
    """API method to delete a task.  Passes request to crud.tasks module"""
    if not (task := crud.tasks.delete(db, id=task_id)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/complete/{task_id}/", response_model=schemas.Task)
async def complete(db: Session = Depends(sqlalchemy_session), task_id: int = None):
    """API method to complete a task.  Passes request to crud.tasks module"""
    if not (task := crud.tasks.complete_task(db, id=task_id)):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
