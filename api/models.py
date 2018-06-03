from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

import math
import datetime

class Tag(models.Model):
    """
    A tag used to associate queries with hosts, and hosts with one another.
    """

    name = models.SlugField(max_length=22, allow_unicode=True, help_text="Descriptive slug name for the tag")

    def __str__(self):
        return self.name

class Host(models.Model):
    """
    One computer.
    """

    node_key = models.CharField(max_length=32, db_index=True, unique=True, help_text="Secret key this host uses to identify itself.")
    identifier = models.CharField(max_length=255, db_index=True, help_text="Unique identifier for this system (usually hostname).")
    last_seen = models.DateTimeField(auto_now_add=True, help_text="Last time this host checked in.")
    invalidate = models.BooleanField(default=False, help_text="Whether this node should be re-enrolled from scratch next time it checks in.")
    architecture = models.CharField(max_length=200, db_index=True, help_text="Machine architecture.", blank=True)
    release = models.CharField(max_length=200, db_index=True, help_text="Operating system release.", blank=True)
    cpu = models.CharField(max_length=200, help_text="Model of CPU installed.", blank=True)
    ram = models.BigIntegerField(help_text="Amount of RAM installed (KiB).", blank=True)
    tags = models.ManyToManyField(Tag, help_text="Only queries tagged with these tags will be run on this host.")

    def __str__(self):
        if self.identifier:
            return self.identifier
        return self.node_key

    def ram_gib(self):
        return math.ceil(self.ram / 1024 / 1024 / 1024)

    def alive(self):
        return self.last_seen > timezone.now() - datetime.timedelta(minutes=30)
    alive.boolean = True

class LogQuery(models.Model):
    """
    Query to be run on all hosts with an intersecting set of tags.
    """

    name = models.CharField(max_length=255, help_text="Descriptive name for the query")
    query = models.CharField(max_length=255, help_text="The query to be executed")
    interval = models.IntegerField(help_text="How often should the query be run (in seconds)?", default=10)
    snapshot = models.BooleanField(help_text="Whether this query should send a report even when the data may not have changed. Useful for time series metrics and keepalives.")
    tags = models.ManyToManyField(Tag, help_text="Only hosts tagged with these tags will run these queries. Specifying no tags makes a query run on all hosts.")

    class Meta:
        verbose_name_plural = "log queries"

    def __str__(self):
        return self.name

class LogEntry(models.Model):
    """
    Logged query result.
    """

    name = models.CharField(max_length=255, db_index=True)
    action = models.CharField(max_length=255)
    output = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    host = models.ForeignKey(Host, db_index=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "log entries"

    def __str__(self):
        return "%s %s on %s" % (self.name, self.action, str(self.host))
