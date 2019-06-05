#region imports..
import warnings
import re
from selenium.webdriver.chrome.options import Options
import sys
from tqdm import tqdm
import math
import requests
import time
import sqlite3
from selenium import webdriver
import pandas as pd


#endregion

#region functions
def login():
	kissanime_user_name = input("enter kissanime user name \n")
	kissanime_user_pw = input("enter  password \n")
	user_name_ip = browser.find_element_by_id('username')
	user_name_ip.clear()
	user_name_ip.send_keys(kissanime_user_name)
	pw_ip = browser.find_element_by_id('password')
	pw_ip.clear()
	pw_ip.send_keys(kissanime_user_pw)
	submit = browser.find_element_by_id('btnSubmit')
	submit.click()
	browser.switch_to.window(browser.window_handles[0])

def episode_file_name_creator(links):
	name = links
	first, last = name.split("?name=")
	name_two = str(last)
	epi_name = name_two
	return epi_name

def download_file(epi_name, url):
	name = epi_name + ".mp4"

	path = name
	r = requests.get(url, stream=True)

	# Total size in bytes.
	total_size = int(r.headers.get('content-length', 0))
	block_size = 1024
	wrote = 0
	with open(path, 'wb') as f:
		for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size // block_size), unit='KB',
						 unit_scale=True):
			wrote = wrote + len(data)
			f.write(data)
	if total_size != 0 and wrote != total_size:
		print("ERROR, something went wrong")
	f.close()


def main_code():
	anime_name = input("enter anime name \n")

#endregion

#region sqlite3 anime_search
	conn = sqlite3.connect('anime_list.db')
	c = conn.cursor()
	c.execute("SELECT * FROM anime_list WHERE anime_name LIKE ? ", ("%" + anime_name + "%",))
	rows = [row[0] for row in c.fetchall()]

	for x in rows:
		print(x + "\n")

	conn.close()

#endregion

#region anime_search
	browser.get("https://kissanime.ru/AdvanceSearch")
	anime_name_refined = input("enter the anime you want from search results \n")
	search_input = browser.find_element_by_css_selector('#animeName')
	search_input.send_keys(anime_name_refined)
#Advanced Search button click
	browser.find_element_by_css_selector("#btnSubmit").click()
	print("searching..... \n")
	browser.implicitly_wait(1)
	print("still searching..... \n")
	exact_match = browser.find_element_by_link_text(anime_name_refined.strip()).get_attribute("href")
	browser.get(exact_match.strip())
	print("match found! \n")
	latest_episode = input("how many latest episodes to download? \n")
	latest_episode = latest_episode.lower()
	if latest_episode == "all":
		latest_episode = 2000
	latest_episode_to_download = int(latest_episode)
#endregion

#region main_code
	list_of_hrefs = []
	list_of_episode_names = []
#get all the href for episodes
	content_blocks = browser.find_elements_by_class_name("listing")

	for block in content_blocks:
		elements = block.find_elements_by_tag_name("a")
		for el in elements:
			list_of_hrefs.append(el.get_attribute("href"))
			list_of_episode_names.append(str(el.get_attribute("text")).strip('\n').strip())
	str_epi_names = str(list_of_episode_names[:latest_episode_to_download])
	formatted_episode_names = re.findall(r"'([^']*)'", str_epi_names)
	for e in formatted_episode_names:
		print(e + "\n")

# trims out href depending upon the no. of episodes
	trimmed_list_of_href = list_of_hrefs[:latest_episode_to_download]
	print("please wait..might take some time")
# get all the href for skip_video_btn
	list_of_skip_ad_hrefs = []
	for epi_link in trimmed_list_of_href:
		browser.get(epi_link)
		skp_ad = browser.find_element_by_css_selector('#formVerify1 > div:nth-child(3) > p:nth-child(1) > a').get_attribute("href")
		list_of_skip_ad_hrefs.append(skp_ad)


# get all the href for click_here_to_download_btn
	rapid_video_links = []
	for rapid_links in list_of_skip_ad_hrefs:
		browser.get(rapid_links)
		clk_to_download = browser.find_element_by_css_selector('#divDownload > a').get_attribute("href")
		rapid_video_links.append(clk_to_download)

# get all the href for rapid_video links
	list_of_mp4 = []
	for video_mp4 in rapid_video_links:
		browser.get(video_mp4)
		final_video_link = browser.find_element_by_css_selector('#button-download').get_attribute("href")
		list_of_mp4.append(final_video_link)
		print("in progress")


	list_of_epi_file_name = []

	anime_epi_list = pd.DataFrame({'Episode Name': list_of_episode_names[:latest_episode_to_download], 'Download Links': list_of_mp4})
	pd.DataFrame(anime_epi_list).to_excel(anime_name_refined.strip()+'.xlsx', header=False, index=False)
	# downloading mp4
	for links in list_of_mp4:
		epi_file_name = episode_file_name_creator(links)
		list_of_epi_file_name.append(epi_file_name)
		# to do create folder for each anime  and store files in that folder
		download_file(epi_file_name, links)
		print(epi_file_name + " downloaded sucessfully")

#endregion

#region browser_setup
chrome_options = Options()
warnings.filterwarnings("ignore", category=DeprecationWarning)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--log-level=3")
browser = webdriver.Chrome('chromedriver.exe', options=chrome_options)
#endregion

#region main code
login_page ='https://kissanime.ru/Login'
browser.get('https://kissanime.ru/Login')
time.sleep(1)
current_url = browser.current_url
while current_url == login_page:
	login()
	browser.implicitly_wait(1)
	new_current_url = browser.current_url
	while new_current_url == "https://kissanime.ru/":
		print("Login Successful")
		main_code()
		sys.exit()

#endregion







