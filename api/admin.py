from django.contrib import admin

from .models import *

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'host_count', 'query_count')

    def host_count(self, tag):
        return tag.host_set.count()
    
    def query_count(self, tag):
        return tag.logquery_set.count()

class LogQueryAdmin(admin.ModelAdmin):
    list_display = ('name', 'query', 'interval')

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('host', 'name', 'action', 'shortened_output', 'created')
    list_filter = ['created','action']

    def shortened_output(self, entry):
        if len(entry.output) > 90:
            return "%s..." % entry.output[:90]
        return entry.output

class LogEntryInline(admin.TabularInline):
    model = LogEntry
    extra = 0 

class HostAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'tag_list', 'release', 'architecture', 'cpu', 'ram_gib', 'last_seen', 'alive')
    list_filter = ['release', 'architecture', 'tags']

    def tag_list(self, host):
        return ", ".join([tag.name for tag in host.tags.all()])

admin.site.register(Host, HostAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(LogQuery, LogQueryAdmin)
admin.site.register(Tag, TagAdmin)
