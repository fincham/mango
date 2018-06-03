from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ObjectDoesNotExist
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.text import slugify

from .models import *

import json
import random
import string
import functools
import hmac

def decode_json_body(fn):
    """
    Decorator to decode JSON test passed in the body of a request.
    """
    @functools.wraps(fn)
    def wrap(request, *args, **kwargs):
        try:
            form = json.loads(request.body.decode('utf-8'))
        except:
            response = {
                "node_invalid": True
            }
            return JsonResponse(response)
        return fn(request, form, *args, **kwargs)
    return wrap

def retrieve_host(fn):
    """
    Decorator to authenticate access to a particular host for a request and make that host available.
    """
    @functools.wraps(fn)
    def wrap(request, form, *args, **kwargs):
        try:
            host = Host.objects.get(node_key=form['node_key'])
            if host.invalidate:
                host.delete()
                raise ObjectDoesNotExist
            host.last_seen = now()
            host.save()
        except ObjectDoesNotExist:
            response = {
                "node_invalid": True
            }
            return JsonResponse(response)
        return fn(request, form, host, *args, **kwargs)
    return wrap

@decode_json_body
@csrf_exempt
@require_http_methods(['POST'])
def enroll(request, form):
    """
    Called by osqueryd during initial configuration of a new node. Returns the node's unique access key, which will be used from then on.
    """

    if hmac.compare_digest(form['enroll_secret'], settings.OSQUERY_ENROLL_SECRET):
        rand = random.SystemRandom();
        node_key = "".join(rand.choice(string.hexdigits) for _ in range(32)).lower() # generate a 128 bit key
        response = {
            "node_key": node_key,
            "node_invalid": False
        }
        Host.objects.create(node_key=node_key, identifier=node_key, ram=0, cpu='', release='', architecture='')
    else:
        response = {
            "node_invalid": True
        }

    return JsonResponse(response)

@decode_json_body
@retrieve_host
@csrf_exempt
@require_http_methods(['POST'])
def config(request, form, host):
    """
    Called by osqueryd during daemon startup to retrieve configuration (such as what queries to be run).
    """

    response = {
        "schedule": {
            "mango_os-version": {
                "query": "SELECT * FROM os_version;",
                "interval": 10
            },
            "mango_system-info": {
                "query": "SELECT * FROM system_info;",
                "interval": 60,
                "snapshot": True # this query is used as a "keepalive"
            },
            "mango_osrelease": {
                "query": "select current_value from system_controls where name = 'kernel.osrelease';",
                "interval": 10
            },
        },
        "node_invalid": False
    }

    for query in LogQuery.objects.filter(tags__in=host.tags.all()):
       response['schedule']['mango_db_%s' % slugify(query.name)] = {
           "query": "%s;" % query.query,
           "interval": query.interval,
           "snapshot": query.snapshot,
        }

    return JsonResponse(response)

@transaction.atomic
@decode_json_body
@retrieve_host
@csrf_exempt
@require_http_methods(['POST'])
def logger(request, form, host):
    """
    Called by osqueryd to report "log results", either diffs to a query or an entire copy of the queried dataset, for snapshots.
    """

    if form['log_type'] == 'result': # a "change" on a query
        host.identifier = form['data'][0]['hostIdentifier']
        for submitted_log_entry in form['data']:
            entry_name = submitted_log_entry['name']
            entry_action = submitted_log_entry['action']
           
            recognised_action = False
            if entry_action == 'added':
                entry_output = submitted_log_entry['columns']
                if entry_name == "mango_os-version":
                    host.release = entry_output['version'].split()[-1].strip('()')
                    recognised_action = True
                elif entry_name == "mango_osrelease":
                    host.architecture = entry_output['current_value'].split('-')[-1]
                    recognised_action = True
            elif entry_action == 'snapshot': # full snapshot query
                entry_outputs = submitted_log_entry['snapshot']
                for entry_output in entry_outputs:
                    if entry_name == "mango_system-info":
                        host.cpu = entry_output['cpu_brand']
                        host.ram = int(entry_output['physical_memory'])
            
            if recognised_action == False and entry_action in ('added', 'removed') and entry_name.startswith('mango_db_'): # just log to the db
                    log_entry = LogEntry(name=entry_name[len('mango_db_'):], action=entry_action, output=repr(entry_output), host=host)
                    log_entry.save()

    host.save()
    response = {
        "node_invalid": host.invalidate
    }
    return JsonResponse(response)
