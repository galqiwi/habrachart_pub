import requests
import re
import time
from datetime import date, timedelta, datetime
import locale
from PIL import Image, ImageDraw, ImageFont
import hashlib

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

def GetCommentPageUrl(user, page):
	return requests.get('https://habr.com/ru/users/{}/comments/page{}/'.format(user, page)).text

def getComments(page_data):
	return zip(re.findall('<time.*\>(.*)\sв\s(\d{2}\:\d{2})</time>', page_data), [int(x.split('>')[1].split('<')[0].replace('–', '-')) for x in re.findall('Общий рейтинг.*\>', page_data)])
	
def IndexUser(user):
	firstPageData = GetCommentPageUrl(user, 1)
	pageFinder = re.findall('/ru/users/{}/comments/page(\d+)/'.format(user), firstPageData)
	if len(pageFinder) == 0:
		return None
	nPages = max([int(x) for x in pageFinder])

	def date_list(page_data):
		out = []
		for i, rate in getComments(page_data):
			date_ = i[0]
			if date_ == "сегодня":
				date_ = date.today().strftime('%d %B %Y')
			if date_ == "вчера":
				date_ = (date.today() - timedelta(days=1)).strftime('%d %B %Y')
			
			out.append([datetime.strptime(date_ + ' ' + i[1], "%d %B %Y %H:%M"), rate])
		return out

	dates = date_list(firstPageData)
	
	for i in range(1, nPages + 1):
		#print(i, nPages)
		dates += date_list(GetCommentPageUrl(user, i))
	return dates

TEXT_FIELD_WIDTH = 200
MARGIN = 40
FIELD_HEIGHT = 2000
FIELD_WIDTH = 1440
NAMEFIELD_SPACE = 100
HOURS_SIZE = 40

def getUserImage(username, image_directory = './'):
	dates = IndexUser(username.lower())
	if dates is None:
		return None

	image = Image.new('RGB', (FIELD_WIDTH + TEXT_FIELD_WIDTH + 2 * MARGIN, FIELD_HEIGHT + 2 * MARGIN + NAMEFIELD_SPACE + HOURS_SIZE), (0, 0, 0))
	draw = ImageDraw.Draw(image)

	"""
	for x in range(0, 1440):
		for y in range(0, 2000):
			draw.point((x + MARGIN + TEXT_FIELD_WIDTH, y + MARGIN), (128, 128, 128))
	"""

	WIDTH = 3;

	font = ImageFont.truetype("sans-serif.ttf", 35)
	font2 = ImageFont.truetype("sans-serif.ttf", 50)
	draw.text((MARGIN + TEXT_FIELD_WIDTH + FIELD_WIDTH / 2 - draw.textsize(username, font2)[0] / 2, MARGIN + NAMEFIELD_SPACE * 0.5 - draw.textsize(username, font2)[1] / 2), username, font=font2)

	for h in range(0, 25, 2):
		x_ = MARGIN + TEXT_FIELD_WIDTH + h / 24 * FIELD_WIDTH
		x = x_ - draw.textsize(str(h), font)[0] / 2
		draw.text((x, MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE), str(h), font=font)
		draw.line([(x_, MARGIN + NAMEFIELD_SPACE), (x_, MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE)], (64, 64, 64), width = WIDTH)

	datetimeNow = datetime.today()

	date_zero = datetime.today() - timedelta(days=FIELD_HEIGHT)
	date_tmp = datetime.strptime(date_zero.strftime('%Y'), '%Y')
	date_tmp += timedelta(days=365.25)
	while date_tmp < datetimeNow:
		y = MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE - (date_tmp - date_zero).days - 35
		draw.text((40, y - draw.textsize(date_tmp.strftime('%d.%m.%Y'), font)[1] / 2), date_tmp.strftime('%d.%m.%Y'), (255, 255, 255), font=font)
		draw.line([(TEXT_FIELD_WIDTH + MARGIN - 1, y), (TEXT_FIELD_WIDTH + MARGIN + FIELD_WIDTH, y)], (64, 64, 64), width = WIDTH)
		date_tmp += timedelta(days=365.25)


	GREEN = (0x80, 0xFF, 0x80)
	RED = (0xFF, 0x80, 0x80)

	draw.line([(TEXT_FIELD_WIDTH + MARGIN - 1, MARGIN - 1 + NAMEFIELD_SPACE), (TEXT_FIELD_WIDTH + MARGIN - 1, MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE)], width = WIDTH)
	draw.line([(TEXT_FIELD_WIDTH + MARGIN + FIELD_WIDTH, MARGIN - 1 + NAMEFIELD_SPACE), (TEXT_FIELD_WIDTH + MARGIN + FIELD_WIDTH, MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE)], width = WIDTH)
	draw.line([(TEXT_FIELD_WIDTH + MARGIN - 1, MARGIN - 1 + NAMEFIELD_SPACE), (TEXT_FIELD_WIDTH + MARGIN + FIELD_WIDTH, MARGIN - 1 + NAMEFIELD_SPACE)], width = WIDTH)
	draw.line([(TEXT_FIELD_WIDTH + MARGIN - 1, MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE), (TEXT_FIELD_WIDTH + MARGIN + FIELD_WIDTH, MARGIN + FIELD_HEIGHT + NAMEFIELD_SPACE)], width = WIDTH)


	"""
	for x in range(0, 1440):
		for y in range(0, 2000):
			draw.point((x + MARGIN + TEXT_FIELD_WIDTH, y + MARGIN), (128, 128, 128))
	"""

	def printCross(x, y, draw, rating):
		#print(rating)
		color = GREEN if rating >= 0 else RED

		#for dx in range(-1, 2):
		#	for dy in range(-1, 2):
		#		draw.point((x + MARGIN + TEXT_FIELD_WIDTH + dx, y + MARGIN + dy), color)

		draw.point((x + MARGIN + TEXT_FIELD_WIDTH + 0, y + MARGIN + 0 + NAMEFIELD_SPACE), color)
		draw.point((x + MARGIN + TEXT_FIELD_WIDTH + 1, y + MARGIN + 0 + NAMEFIELD_SPACE), color)
		draw.point((x + MARGIN + TEXT_FIELD_WIDTH - 1, y + MARGIN + 0 + NAMEFIELD_SPACE), color)
		draw.point((x + MARGIN + TEXT_FIELD_WIDTH + 0, y + MARGIN + 1 + NAMEFIELD_SPACE), color)
		draw.point((x + MARGIN + TEXT_FIELD_WIDTH + 0, y + MARGIN - 1 + NAMEFIELD_SPACE), color)

	for date in dates:
		y = (datetimeNow - date[0]).days + 1;
		x = date[0].hour * 60 + date[0].minute
		printCross(x, y, draw, date[1])

	image.save(image_directory + hashlib.md5(username.lower().encode('utf-8')).hexdigest() + '.png', 'PNG')
	return hashlib.md5(username.lower().encode('utf-8')).hexdigest() + '.png'

getUserImage('galqiwi')