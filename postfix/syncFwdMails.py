#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xmlrpclib
api = xmlrpclib.ServerProxy('https://rpc.gandi.net/xmlrpc/')
apikey = open("/etc/postfix/Gandi.ApiKey").read().strip()

domains=[]
for entry in api.domain.list(apikey):
	print "* Found " + entry['fqdn']
	domains.append(entry['fqdn'])

gandi={}
for domain in domains:
	for entry in api.domain.forward.list(apikey, domain):
		gandi[entry['source']+"@"+domain] = entry['destinations']

virtual={}
for line in open('/etc/postfix/virtual', 'ro'):
	if "DOMAIN" in line:
		domain=line.split()[0].strip('#\n')
	else:
		if line != "\n":
			if "#" in line:
				if "GANDI" in line:
					source, destinations=line.split()[0:2]
					source=source.lstrip('#')
				else:
					continue
			else:
				source, destinations=line.split()

			if "@" not in source:
				source=source+"@"+domain
			virtual[source]=destinations.split(',')

DELETE=set.difference(set(gandi), set(virtual))
CREATE=set.difference(set(virtual), set(gandi))

for email in sorted(set.union(set(gandi), set(virtual))):
	alias, domain=email.split('@')
	if domain not in domains:
		print "[ ERROR ] " + email + ": «" + domain + "» not managed."
		continue

	elif email in CREATE:
		# Add entry...
		api.domain.forward.create(apikey, domain, alias, {'destinations':virtual[email]})
		print "[CREATED] " + alias + "@" + domain + "\r\t\t\t\t\t → " + ','.join(virtual[email])
		continue

	elif email in DELETE:
		# Remove entry...
		api.domain.forward.delete(apikey, domain, alias)
		print "[REMOVED] " + alias + "@" + domain + "\r\t\t\t\t\t (" + ','.join(gandi[email]) + ")"
		continue

	elif virtual[email] != gandi[email]:
		# Update entry...
		api.domain.forward.update(apikey, domain, alias, {'destinations':virtual[email]})
		print "[UPDATED] " + alias + "@" + domain + "\r\t\t\t\t\t→ " + ','.join(virtual[email]) + " (" + ','.join(gandi[email]) + ")"

	else:
		print "          " + alias + "@" + domain + "\r\t\t\t\t\t→ " + ','.join(virtual[email])

