from models.logs import Log

def get_all_logs():
    return Log.query.all()
