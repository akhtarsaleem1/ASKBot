from askbot.database import engine
from sqlmodel import Session
from askbot.services.analytics import AnalyticsFetcher

def run():
    with Session(engine) as session:
        fetcher = AnalyticsFetcher()
        fetcher.sync_metrics(session)
        print("Sync complete.")

if __name__ == "__main__":
    run()
