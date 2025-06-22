from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import atexit
from add_notices import add_notices_to_db
import pytz

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    
    # Add job to update notices every 6 hours
    scheduler.add_job(
        func=add_notices_to_db,
        trigger=IntervalTrigger(hours=6),
        id='update_notices_job',
        name='Update notices from PTU website',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown()) 