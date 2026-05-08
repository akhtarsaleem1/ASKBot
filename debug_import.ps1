$env:PYTHONPATH = "D:\Software\ASKBot\.python-packages;D:\Software\ASKBot"
$py = "C:\Users\ASK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -c "from askbot.database import engine; from askbot.models import Setting; from sqlmodel import Session, select; session = Session(engine); print([(s.key, s.value) for s in session.exec(select(Setting)).all()])"
