from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal, Base
from models import User, Journey, FareLog
import uuid
import datetime

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Railway POC Backend")

# CORS middleware - allows requests from any origin (required for local WiFi access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "Railway POC Backend Running", "version": "1.0"}


@app.post("/register_user")
def register_user():
    """
    Register a new user with unique user_id and ₹100 starting wallet balance.
    Called once by Android app on first launch.
    """
    db = SessionLocal()
    try:
        user_id = str(uuid.uuid4())
        new_user = User(user_id=user_id, wallet_balance=100.0)
        db.add(new_user)
        db.commit()
        return {
            "user_id": user_id,
            "wallet_balance": 100.0,
            "message": "User registered successfully"
        }
    finally:
        db.close()


@app.post("/journey_start")
def journey_start(user_id: str):
    """
    Start a new journey when Raspberry Pi detects BLE proximity.
    Creates ACTIVE journey record.
    """
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user already has an active journey
        active_journey = db.query(Journey).filter(
            Journey.user_id == user_id,
            Journey.status == "ACTIVE"
        ).first()

        if active_journey:
            return {
                "message": "Journey already active",
                "journey_id": active_journey.journey_id,
                "start_time": active_journey.start_time
            }

        # Create new journey
        journey_id = str(uuid.uuid4())
        new_journey = Journey(
            journey_id=journey_id,
            user_id=user_id,
            status="ACTIVE"
        )
        db.add(new_journey)
        db.commit()

        return {
            "message": "Journey started",
            "journey_id": journey_id,
            "user_id": user_id,
            "start_time": new_journey.start_time
        }
    finally:
        db.close()


@app.post("/journey_end")
def journey_end(user_id: str):
    """
    End journey when Raspberry Pi detects BLE exit (out of range).
    Deducts ₹20 fare from wallet and logs transaction.
    """
    db = SessionLocal()
    try:
        # Find active journey for this user
        active_journey = db.query(Journey).filter(
            Journey.user_id == user_id,
            Journey.status == "ACTIVE"
        ).first()

        if not active_journey:
            raise HTTPException(
                status_code=404, detail="No active journey found")

        # Get user and deduct fare
        user = db.query(User).filter(User.user_id == user_id).first()
        fare_amount = 20.0

        # Deduct fare (allow negative balance for POC - in production would check minimum)
        user.wallet_balance -= fare_amount

        # Mark journey as ended
        active_journey.status = "ENDED"
        active_journey.end_time = datetime.datetime.utcnow()

        # Log fare deduction
        fare_log = FareLog(
            user_id=user_id,
            journey_id=active_journey.journey_id,
            amount=fare_amount,
            description="Auto fare deduction on journey end"
        )
        db.add(fare_log)
        db.commit()

        return {
            "message": "Journey ended, fare deducted",
            "journey_id": active_journey.journey_id,
            "fare_amount": fare_amount,
            "remaining_balance": user.wallet_balance,
            "journey_duration": str(active_journey.end_time - active_journey.start_time)
        }
    finally:
        db.close()


@app.get("/wallet_balance")
def wallet_balance(user_id: str):
    """
    Get current wallet balance for a user.
    Polled by Android app every 5 seconds.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has active journey
        active_journey = db.query(Journey).filter(
            Journey.user_id == user_id,
            Journey.status == "ACTIVE"
        ).first()

        return {
            "user_id": user_id,
            "wallet_balance": user.wallet_balance,
            "journey_active": active_journey is not None
        }
    finally:
        db.close()


@app.post("/add_funds")
def add_funds(user_id: str):
    """
    Add ₹100 to user wallet.
    Called when user presses 'Add Funds' button in Android app.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add fixed ₹100
        add_amount = 100.0
        user.wallet_balance += add_amount

        # Log transaction
        fare_log = FareLog(
            user_id=user_id,
            journey_id="NONE",
            amount=add_amount,
            description="Funds added by user"
        )
        db.add(fare_log)
        db.commit()

        return {
            "message": "Funds added successfully",
            "amount_added": add_amount,
            "new_balance": user.wallet_balance
        }
    finally:
        db.close()
