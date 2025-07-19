#!/usr/bin/env python3
"""
Debug script to check and fix meter readings for cumulative units display
"""

from app import app, db, MeterReading, ElectricityBill, User, RentPayment
from datetime import datetime

def debug_meter_readings():
    with app.app_context():
        print("=== METER READINGS DEBUG ===")
        
        # Get all users
        users = User.query.filter_by(is_admin=False).all()
        
        for user in users:
            print(f"\n--- User: {user.username} ---")
            
            # Get meter readings for this user
            readings = MeterReading.query.filter_by(renter_id=user.id).order_by(
                MeterReading.year.asc(), MeterReading.month.asc()
            ).all()
            
            print("Meter Readings:")
            for reading in readings:
                print(f"  {reading.month:02d}/{reading.year}: Current={reading.current_reading}, Previous={reading.previous_reading}, Consumed={reading.units_consumed}")
            
            # Get electricity bills for this user
            bills = ElectricityBill.query.filter_by(renter_id=user.id, is_paid=True).order_by(
                ElectricityBill.year.asc(), ElectricityBill.month.asc()
            ).all()
            
            print("Paid Electricity Bills:")
            cumulative = 0
            for bill in bills:
                meter_reading = bill.meter_reading.current_reading if bill.meter_reading else "NO METER"
                cumulative += float(bill.units_consumed or 0)
                print(f"  {bill.month:02d}/{bill.year}: Units={bill.units_consumed}, Meter={meter_reading}, Cumulative Sum={cumulative}")
            
            # Get rent payments for this user
            rent_payments = RentPayment.query.filter_by(renter_id=user.id, is_paid=True).order_by(
                RentPayment.year.asc(), RentPayment.month.asc()
            ).all()
            
            print("Rent Payments:")
            for payment in rent_payments:
                print(f"  {payment.month:02d}/{payment.year}: Amount={payment.amount}, Date={payment.payment_date}")

def fix_meter_readings_cumulative():
    """
    Fix meter readings to have proper cumulative values
    This assumes that current_reading should be cumulative from a starting point
    """
    with app.app_context():
        print("=== FIXING METER READINGS ===")
        
        users = User.query.filter_by(is_admin=False).all()
        
        for user in users:
            print(f"\n--- Fixing User: {user.username} ---")
            
            # Get all meter readings for this user, ordered by date
            readings = MeterReading.query.filter_by(renter_id=user.id).order_by(
                MeterReading.year.asc(), MeterReading.month.asc()
            ).all()
            
            if not readings:
                print("  No meter readings found")
                continue
            
            # Start with the first reading as the base
            cumulative = 0
            for i, reading in enumerate(readings):
                if i == 0:
                    # First reading - use its current_reading as starting point
                    cumulative = float(reading.current_reading or 0)
                    if cumulative == 0:
                        # If first reading is 0, set it to a reasonable starting value
                        cumulative = 3500  # Example starting point like in your note
                        reading.current_reading = cumulative
                else:
                    # Add the units consumed to get new cumulative total
                    cumulative += float(reading.units_consumed or 0)
                    reading.current_reading = cumulative
                
                print(f"  {reading.month:02d}/{reading.year}: Set current_reading to {cumulative}")
            
            # Commit changes
            db.session.commit()
            print(f"  Updated {len(readings)} meter readings for {user.username}")

if __name__ == "__main__":
    print("1. Debug current meter readings")
    print("2. Fix meter readings to be cumulative")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        debug_meter_readings()
    elif choice == "2":
        confirm = input("This will modify the database. Are you sure? (yes/no): ").strip().lower()
        if confirm == "yes":
            fix_meter_readings_cumulative()
            print("\nMeter readings fixed! Run option 1 to verify.")
        else:
            print("Operation cancelled")
    else:
        print("Invalid choice")
