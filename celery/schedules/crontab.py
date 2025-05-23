class crontab:
    def __init__(self, minute='*', hour='*'):
        self.minute = minute
        self.hour = hour
    def __str__(self):
        return f"{self.minute} {self.hour}"