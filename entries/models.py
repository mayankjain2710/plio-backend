from django.conf import settings
from django.db import models
from plio.models import Plio, Item
from experiments.models import Experiment
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from entries.config import event_type_choices


class Session(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    plio = models.ForeignKey(Plio, on_delete=models.CASCADE)
    experiment = models.ForeignKey(Experiment, on_delete=models.DO_NOTHING, null=True)
    retention = models.TextField(default="")
    watch_time = models.FloatField(default=0)
    has_video_played = models.BooleanField(default=False)
    is_first = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "session"
        ordering = ["-id"]
    
    def save(self, *args, **kwargs):
        # Round the watch_time to 2 decimal places before saving
        self.watch_time = round(self.watch_time, 2)
        super(Session, self).save(*args, **kwargs)

    @property
    def last_session(self):
        """Get the session previous to this session for the same user-plio pair"""
        return (
            Session.objects.filter(plio_id=self.plio_id)
            .filter(user_id=self.user_id)
            .filter(id__lt=self.id)
            .first()
        )

    @property
    def last_global_event(self):
        """Returns the most recent event tied to a particular user-plio pair"""
        # find the most recent event for this session
        current_last_event = self.event_set.first()
        if current_last_event:
            return current_last_event

        # if there are no events in this session, find the most recent event in
        # the past sessions

        if not self.last_session:
            # this is the first session for the user-plio pair - no last event
            return None

        # either return the most recent event tied to the last session or
        # the last_event property of the last session in case no new events are
        # tied to the last session
        return (
            self.last_session.event_set.first() or self.last_session.last_global_event
        )


class SessionAnswer(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    answer = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "session_answer"
        ordering = ["item__time"]


class Event(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    type = models.CharField(max_length=255, choices=event_type_choices)
    player_time = models.FloatField()
    details = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event"
        ordering = ["-updated_at"]
