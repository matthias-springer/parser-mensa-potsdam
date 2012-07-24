#!/usr/bin/python
# -*- encoding: utf-8 -*-
import cgitb
import libxml2
import datetime
import os
from urllib import urlopen
from bs4 import BeautifulSoup

cgitb.enable()

# Helper arrays and dictionaries for processing and formating HTML data
months = ["Januar", "Feburar", "Mä", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
months_dict = {m : str(months.index(m) + 1).zfill(2) for m in months}
days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
days_dict = {d + ", " : "" for d in days}
date_dict = dict(days_dict.items() + months_dict.items())
prices = {1 : "1.20", 2 : "2.00", 3 : "2.50", 4 : "2.30"}
xhtml_namespace = "namespace-uri() = 'http://www.w3.org/1999/xhtml'"

# Create XPath query string for a CSS class
def create_xpath_for_class(css_class):
	return "*[local-name() = 'html' and "  + xhtml_namespace + "]//*[local-name() = 'table' and " + xhtml_namespace + " and contains(@class, 'bill_of_fare')]//*[" + xhtml_namespace + " and contains(@class, '" + css_class + "')]"

# Query mensa with URL
def do_mensa(url):
	xml_data = libxml2.parseDoc(BeautifulSoup(urlopen(url).read()).prettify().encode("UTF-8"))
	
	dates = xml_data.xpathEval(create_xpath_for_class("date"))
	dates = map(lambda item: "-".join(reversed(reduce(lambda i, m: i.replace(*m), date_dict.iteritems(), item.getContent().strip()).replace(".", "").split(" "))), dates)

	meals = [xml_data.xpathEval(create_xpath_for_class("text" + meal_id)) for meal_id in ["1", "2", "3", "4"]]
	meals = map(lambda meals: map(lambda meal: meal.getContent().strip().replace("\n", "").replace("  ", ""), meals), meals)
		
	xml_return = ""

	for e in range(len(meals[1])):
		if e >= len(dates):
			xml_return += "<day date=\"" + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d") + "\">"
		else:
			xml_return += "<day date=\"" + dates[e] + "\">"
			
		for meal_id in prices.keys():
			if len(meals[meal_id - 1][e]) > 0:
				# Generate XML for meal
				xml_return += "<category name=\"Essen " + str(meal_id) + "\"><meal><name>" + meals[meal_id - 1][e] + "</name><note></note><price>" + prices[meal_id] + "</price></meal></category>"
		
		xml_return += "</day>"
		
	return xml_return

request_uri = os.environ['REQUEST_URI']
# Generate CGI output
xml_return = """Content-Type: text/xml

<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE cafeteria SYSTEM \"http://om.altimos.de/open-mensa-v1.dtd\">
<cafeteria version=\"1.0\">"""

xml_return += do_mensa("http://www.studentenwerk-potsdam.de/speiseplan.html")

mensa = request_uri.split("?mensa=")
if len(mensa) > 1:
	# Currently supported: golm, pappelallee, friedrich-ebert-strasse, brandenburg, wildau, griebnitzsee
	# Currently NOT supported: am-neuen-palais
	xml_return += do_mensa("http://www.studentenwerk-potsdam.de/mensa-" + mensa[1] + ".html")

xml_return += "</cafeteria>"
print(xml_return)


