import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.database import get_db
from app.models.models import Category, Prediction, User

from sqlalchemy.orm import selectinload

router = APIRouter()

class UserOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class PredictionCreate(BaseModel):
    creator_id: int
    description: str
    confidence: float
    category_id: int

class CategoryOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class PredictionOut(PredictionCreate):
    id: int
    status: str
    outcome: Optional[bool]
    created_at: datetime.datetime
    creator: UserOut
    category: CategoryOut
    opponent: Optional[UserOut] = None
    class Config:
        orm_mode = True

class PredictionAccept(BaseModel):
    user_id: int

@router.post("/api/predictions/{prediction_id}/accept", response_model=PredictionOut)
async def accept_prediction(
    prediction_id: int,
    acceptance: PredictionAccept,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    db_prediction = result.scalars().first()
    if not db_prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    if db_prediction.status != "PENDING":
        raise HTTPException(status_code=400, detail="This bet is not pending acceptance.")
    if db_prediction.creator_id == acceptance.user_id:
        raise HTTPException(status_code=400, detail="You cannot accept your own bet.")
    db_prediction.opponent_id = acceptance.user_id
    db_prediction.status = "OPEN"
    await db.commit()
    # Re-fetch the prediction with the relationships loaded

    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.creator), selectinload(Prediction.category), selectinload(Prediction.opponent))
        .where(Prediction.id == db_prediction.id)
    )

    accepted_prediction = result.scalars().first()
    return accepted_prediction

class PredictionResolve(BaseModel):
    outcome: bool

@router.post("/api/predictions", response_model=PredictionOut)
async def create_prediction(
    prediction: PredictionCreate, db: AsyncSession = Depends(get_db)
):

    db_prediction = Prediction(**prediction.dict())
    db.add(db_prediction)
    await db.commit()
    # Re-fetch the prediction with the relationships loaded

    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.creator), selectinload(Prediction.category), selectinload(Prediction.opponent))
        .where(Prediction.id == db_prediction.id)
    )

    new_prediction = result.scalars().first()
    return new_prediction

@router.delete("/api/predictions/{prediction_id}", status_code=204)
async def delete_prediction(prediction_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    db_prediction = result.scalars().first()
    if not db_prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    await db.delete(db_prediction)
    await db.commit()
    return

@router.get("/api/predictions", response_model=List[PredictionOut])
async def get_predictions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.creator), selectinload(Prediction.category), selectinload(Prediction.opponent))
    )
    predictions = result.scalars().all()
    return predictions

@router.post("/api/predictions/{prediction_id}/resolve", response_model=PredictionOut)
async def resolve_prediction(
    prediction_id: int,
    prediction_resolve: PredictionResolve,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    db_prediction = result.scalars().first()
    if not db_prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    db_prediction.outcome = prediction_resolve.outcome
    db_prediction.status = "RESOLVED"
    await db.commit()
    # Re-fetch the prediction with the relationships loaded

    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.creator), selectinload(Prediction.category), selectinload(Prediction.opponent))
        .where(Prediction.id == db_prediction.id)
    )

    resolved_prediction = result.scalars().first()
    return resolved_prediction

@router.post("/api/predictions/{prediction_id}/redeem", response_model=PredictionOut)
async def redeem_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    db_prediction = result.scalars().first()
    if not db_prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    db_prediction.status = "REDEEMED"
    await db.commit()
    # Re-fetch the prediction with the relationships loaded

    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.creator), selectinload(Prediction.category), selectinload(Prediction.opponent))
        .where(Prediction.id == db_prediction.id)
    )

    redeemed_prediction = result.scalars().first()
    return redeemed_prediction
from collections import defaultdict

@router.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Get all users for name mapping
    user_result = await db.execute(select(User))
    users = user_result.scalars().all()
    user_map = {user.id: user.name for user in users}
    # Get all resolved predictions
    prediction_result = await db.execute(
        select(Prediction).where(Prediction.status == "RESOLVED")
    )
    predictions = prediction_result.scalars().all()
    
    # Calculate gross debts
    debts = defaultdict(float) # Key: (debtor_id, creditor_id)
    for p in predictions:
        # Skip predictions that don't have an opponent
        if p.opponent_id is None:
            continue
        if p.confidence >= 0.5:
            odds_ratio = p.confidence / (1 - p.confidence)
            if p.outcome:  # Creator wins
                debtor_id = p.opponent_id
                creditor_id = p.creator_id
                amount = 1.0
            else:  # Creator loses
                debtor_id = p.creator_id
                creditor_id = p.opponent_id
                amount = odds_ratio
        else:  # p.confidence < 0.5
            odds_ratio = (1 - p.confidence) / p.confidence
            if p.outcome:  # Creator wins
                debtor_id = p.opponent_id
                creditor_id = p.creator_id
                amount = odds_ratio
            else:  # Creator loses
                debtor_id = p.creator_id
                creditor_id = p.opponent_id
                amount = 1.0
        
        debts[(debtor_id, creditor_id)] += amount
    # Format the response
    formatted_debts = [
        {
            "debtor": user_map.get(debtor_id, "Unknown"),
            "creditor": user_map.get(creditor_id, "Unknown"),
            "amount": round(amount, 2),
        }
        for (debtor_id, creditor_id), amount in debts.items() if amount > 0
    ]

    return formatted_debts

class TrophyPrediction(BaseModel):
    description: str
    units: float

class CategoryStat(BaseModel):
    wins: int
    losses: int

class UserStats(BaseModel):
    id: int
    name: str
    wins: int
    losses: int
    net_units: float
    biggest_upset: Optional[TrophyPrediction] = None
    worst_beat: Optional[TrophyPrediction] = None
    by_category: dict[str, CategoryStat]

def calculate_units(prediction: Prediction):
    if prediction.confidence >= 0.5:
        odds_ratio = prediction.confidence / (1 - prediction.confidence)
        if prediction.outcome: # Creator wins
            return 1.0
        else: # Creator loses
            return -odds_ratio
    else: # prediction.confidence < 0.5
        odds_ratio = (1 - prediction.confidence) / prediction.confidence
        if prediction.outcome: # Creator wins
            return odds_ratio
        else: # Creator loses
            return -1.0

@router.get("/api/user-stats", response_model=list[UserStats])
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()

    predictions_result = await db.execute(
        select(Prediction)
        .where(Prediction.status.in_(["RESOLVED", "REDEEMED"]))
        .options(
            selectinload(Prediction.creator),
            selectinload(Prediction.opponent),
            selectinload(Prediction.category),
        )
    )
    predictions = predictions_result.scalars().all()

    stats = {
        user.id: UserStats(
            id=user.id,
            name=user.name,
            wins=0,
            losses=0,
            net_units=0.0,
            by_category={},
        )
        for user in users
    }

    for p in predictions:
        if p.opponent_id is None:
            continue

        units_for_creator = calculate_units(p)
        
        # Update stats for creator
        stats[p.creator_id].net_units += units_for_creator
        if units_for_creator > 0:
            stats[p.creator_id].wins += 1
            if not stats[p.creator_id].biggest_upset or units_for_creator > stats[p.creator_id].biggest_upset.units:
                stats[p.creator_id].biggest_upset = TrophyPrediction(description=p.description, units=units_for_creator)
        else:
            stats[p.creator_id].losses += 1
            if not stats[p.creator_id].worst_beat or units_for_creator < stats[p.creator_id].worst_beat.units:
                 stats[p.creator_id].worst_beat = TrophyPrediction(description=p.description, units=units_for_creator)

        # Update stats for opponent
        stats[p.opponent_id].net_units -= units_for_creator
        if units_for_creator < 0:
             stats[p.opponent_id].wins += 1
             if not stats[p.opponent_id].biggest_upset or -units_for_creator > stats[p.opponent_id].biggest_upset.units:
                 stats[p.opponent_id].biggest_upset = TrophyPrediction(description=p.description, units=-units_for_creator)
        else:
            stats[p.opponent_id].losses += 1
            if not stats[p.opponent_id].worst_beat or -units_for_creator < stats[p.opponent_id].worst_beat.units:
                 stats[p.opponent_id].worst_beat = TrophyPrediction(description=p.description, units=-units_for_creator)


        # --- W/L by Category (no change from before) ---
        category_name = p.category.name
        creator_wins = p.outcome
        opponent_wins = not p.outcome

        # Creator category stats
        if category_name not in stats[p.creator_id].by_category:
            stats[p.creator_id].by_category[category_name] = CategoryStat(wins=0, losses=0)
        if creator_wins:
            stats[p.creator_id].by_category[category_name].wins += 1
        else:
            stats[p.creator_id].by_category[category_name].losses += 1
        
        # Opponent category stats
        if category_name not in stats[p.opponent_id].by_category:
            stats[p.opponent_id].by_category[category_name] = CategoryStat(wins=0, losses=0)
        if opponent_wins:
            stats[p.opponent_id].by_category[category_name].wins += 1
        else:
            stats[p.opponent_id].by_category[category_name].losses += 1

    return list(stats.values())
