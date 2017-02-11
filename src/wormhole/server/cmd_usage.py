from __future__ import print_function, unicode_literals
import os, time
from collections import defaultdict
import click
from humanize import naturalsize
from .database import get_db

def abbrev(t):
    if t is None:
        return "-"
    if t > 1.0:
        return "%.3fs" % t
    if t > 1e-3:
        return "%.1fms" % (t*1e3)
    return "%.1fus" % (t*1e6)


def print_event(event):
    event_type, started, result, total_bytes, waiting_time, total_time = event
    followthrough = None
    if waiting_time and total_time:
        followthrough = total_time - waiting_time
    print("%17s: total=%7s wait=%7s ft=%7s size=%s (%s)" %
          ("%s-%s" % (event_type, result),
           abbrev(total_time),
           abbrev(waiting_time),
           abbrev(followthrough),
           naturalsize(total_bytes),
           time.ctime(started),
          ))

def show_usage(args):
    print("closed for renovation")
    return 0
    if not os.path.exists("relay.sqlite"):
        raise click.UsageError(
            "cannot find relay.sqlite, please run from the server directory"
        )
    oldest = None
    newest = None
    rendezvous_counters = defaultdict(int)
    transit_counters = defaultdict(int)
    total_transit_bytes = 0
    db = get_db("relay.sqlite")
    c = db.execute("SELECT * FROM `usage`"
                   " ORDER BY `started` ASC LIMIT ?",
                   (args.n,))
    for row in c.fetchall():
        if row["type"] == "rendezvous":
            counters = rendezvous_counters
        elif row["type"] == "transit":
            counters = transit_counters
            total_transit_bytes += row["total_bytes"]
        else:
            continue
        counters["total"] += 1
        counters[row["result"]] += 1
        if oldest is None or row["started"] < oldest:
            oldest = row["started"]
        if newest is None or row["started"] > newest:
            newest = row["started"]
        event = (row["type"], row["started"], row["result"],
                 row["total_bytes"], row["waiting_time"], row["total_time"])
        print_event(event)
    if rendezvous_counters["total"] or transit_counters["total"]:
        print("---")
        print("(most recent started %s ago)" % abbrev(time.time() - newest))
    if rendezvous_counters["total"]:
        print("rendezvous events:")
        counters = rendezvous_counters
        elapsed = time.time() - oldest
        total = counters["total"]
        print(" %d events in %s (%.2f per hour)" % (total, abbrev(elapsed),
                                                    (3600 * total / elapsed)))
        print("", ", ".join(["%s=%d (%d%%)" %
                             (k, counters[k], (100.0 * counters[k] / total))
                             for k in sorted(counters)
                             if k != "total"]))
    if transit_counters["total"]:
        print("transit events:")
        counters = transit_counters
        elapsed = time.time() - oldest
        total = counters["total"]
        print(" %d events in %s (%.2f per hour)" % (total, abbrev(elapsed),
                                                    (3600 * total / elapsed)))
        rate = total_transit_bytes / elapsed
        print(" %s total bytes, %sps" % (naturalsize(total_transit_bytes),
                                         naturalsize(rate)))
        print("", ", ".join(["%s=%d (%d%%)" %
                             (k, counters[k], (100.0 * counters[k] / total))
                             for k in sorted(counters)
                             if k != "total"]))
    return 0

def tail_usage(args):
    if not os.path.exists("relay.sqlite"):
        raise click.UsageError(
            "cannot find relay.sqlite, please run from the server directory"
        )
    db = get_db("relay.sqlite")
    # we don't seem to have unique row IDs, so this is an inaccurate and
    # inefficient hack
    seen = set()
    try:
        while True:
            old = time.time() - 2*60*60
            c = db.execute("SELECT * FROM `usage`"
                           " WHERE `started` > ?"
                           " ORDER BY `started` ASC", (old,))
            for row in c.fetchall():
                event = (row["type"], row["started"], row["result"],
                         row["total_bytes"], row["waiting_time"],
                         row["total_time"])
                if event not in seen:
                    print_event(event)
                    seen.add(event)
            time.sleep(2)
    except KeyboardInterrupt:
        return 0
    return 0

def list_apps(args):
    if not os.path.exists("relay.sqlite"):
        raise click.UsageError(
            "cannot find relay.sqlite, please run from the server directory"
        )
    db = get_db("relay.sqlite")
    def q(query, values=()):
        return list(db.execute(query, values).fetchone().values())
    apps = set()
    apps.update(q("SELECT DISTINCT(`app_id`) FROM `nameplates`"))
    apps.update(q("SELECT DISTINCT(`app_id`) FROM `mailboxes`"))
    apps.update(q("SELECT DISTINCT(`app_id`) FROM `messages`"))
    apps = sorted(apps)
    if apps:
        print("nameplates mailboxes messages  app_id")
        print("---------- --------- --------  ------")
    else:
        print("no active apps")
    for app_id in apps:
        num_nameplates = q("SELECT COUNT() FROM `nameplates` WHERE `app_id`=?",
                           (app_id,))[0]
        num_mailboxes = q("SELECT COUNT() FROM `nameplates` WHERE `app_id`=?",
                          (app_id,))[0]
        num_messages = q("SELECT COUNT() FROM `nameplates` WHERE `app_id`=?",
                         (app_id,))[0]
        print("%10d %9d %8d  %s" % (num_nameplates, num_mailboxes,
                                    num_messages, app_id))

def list_nameplates(args):
    if not os.path.exists("relay.sqlite"):
        raise click.UsageError(
            "cannot find relay.sqlite, please run from the server directory"
        )
    db = get_db("relay.sqlite")

    id_to_name = {}
    for row in db.execute("SELECT * FROM `nameplates`").fetchall():
        id_to_name[row["id"]] = (row["app_id"], row["name"])

    nameplates = defaultdict(lambda: defaultdict(set)) # app->{name->{sides}}
    for row in db.execute("SELECT * FROM `nameplate_sides`").fetchall():
        app_id, name = id_to_name[row["nameplates_id"]]
        nameplates[app_id][name].add( (row["claimed"], row["added"]) )

    now = time.time()
    for app_id in sorted(nameplates):
        print("APP_ID:", app_id)
        for name in sorted(nameplates[app_id]):
            sides = nameplates[app_id][name]
            age = int(now - min([added for (claimed, added) in sides]))
            status = "weird"
            if len(sides) == 1:
                status = "lonely"
            elif len(sides) == 2:
                status = "open"
                if False in [claimed for (claimed, added) in sides]:
                    status = "half-closed"
            elif len(sides) > 2:
                status = "crowded"
            print(" %s: %s (created %ss ago)" % (name, status, age))
    return 0
