#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xmlrpclib
api = xmlrpclib.ServerProxy('https://rpc.gandi.net/xmlrpc/')
apikey = open("/etc/postfix/Gandi.ApiKey").read().strip()

virtual="/etc/postfix/virtual"

domains={}
for entry in api.domain.list(apikey):
	print "Found " + entry['fqdn']
	domains[entry['fqdn']]=None

for line in open(virtual):
	if "#" not in line and "DOMAIN" not in line and line != "\n":
		words=line.split()
		words[:1]=words[0].split("@")
		try:
			alias, domain, email= words[0],words[1],words[2]

			if domain not in domains.keys():
				print "[ ERROR ] " + alias + "@" + domain + " " + email + ": «" + domain + "» not managed"
				continue

			elif domains[domain] is None:
				domains[domain] = api.domain.forward.list(apikey, domain)

			found=False
			for entry in domains[domain][:]:
				if alias in entry.values():
					found=True
					if email not in entry['destinations']:
						try:
							api.domain.forward.update(apikey, domain, alias, {'destinations':email.split(',')})
							print "[UPDATED] " + alias + "@" + domain + "\r\t\t\t\t\t→ " + email + " (" + ','.join(entry['destinations']) + ")"
						except:
							print "[ ERROR ] " + alias + "@" + domain + "\r\t\t\t\t\t→ " + email
					else:
						print "          " + alias + "@" + domain + "\r\t\t\t\t\t→ " + email

			if not found:
				try:
					api.domain.forward.create(apikey, domain, alias, {'destinations':email.split(',')})
					print "[CREATED] " + alias + "@" + domain + "\r\t\t\t\t\t→ " + email
				except:
					print "[ ERROR ] " + alias + "@" + domain + "\r\t\t\t\t\t→ " + email

		except:
			print "[virtual] bad entry: " + line

