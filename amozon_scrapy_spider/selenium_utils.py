import string
import time
import zipfile
from typing import List
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 创建Chrome浏览器对象


# 改成一个对象来封装也挺好的
RETRY_TIME = 4


def webdriver_get(driver, url, retry_time=4, wait_time=5):
	html_content = '<html><head><meta name="color-scheme" content="light dark"></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">Request was throttled. Please wait a moment and refresh the page</pre></body></html>'
	# 打开网页
	# driver.implicitly_wait(wait_time)  # 设置等待时间为10秒
	driver.get(url)
	time.sleep(0.5)
	for i in range(retry_time):
		if driver.page_source == html_content:
			driver.refresh()
			time.sleep(0.1)
		else:
			return driver
	print("重试多次后还是失败了！")
	return driver


def get_base_url(url):
	parsed_url = urlparse(url)
	base_url = parsed_url.scheme + '://' + parsed_url.netloc
	return base_url


# 切换语言
def change_en(driver):
	# 切换语言
	change_language = driver.find_element(By.XPATH, '//*[@id="icp-nav-flyout"]')
	change_language.click()
	
	selected_en = driver.find_element(By.XPATH, '//*[@id="icp-language-settings"]/div[2]/div/label/span/span')
	selected_en.click()
	
	save_change = driver.find_element(By.XPATH, '//*[@id="icp-save-button"]/span/input')
	save_change.click()
	return driver


def scrol_to_buttom(driver, wait_time=1):
	last_height = driver.execute_script('return document.body.scrollHeight')
	while True:
		# 执行JavaScript，对页面进行滚动
		driver.execute_script('window.scrollTo(0, document.body.scrollHeight + 550);')
		# driver.execute_script("window.scrollBy(0, -500);")
		
		# 等待页面加载完成
		time.sleep(wait_time)  # 强心等了一秒（等待把东西加载出来）
		# 判断是否还有可以滚动的内容
		new_height = driver.execute_script('return document.body.scrollHeight')
		
		if new_height == last_height:
			break
		else:
			last_height = new_height
	print("已经滚动完了所有内容")


def get_right_category_urls(driver) -> List[List]:  # category_name, url
	right_tab_list = driver.find_elements(By.XPATH, '//div[@role="group"]/div')
	category_url_list = []
	for i in right_tab_list:
		try:
			result = i.find_element(By.XPATH, 'a')
			url = result.get_attribute("href")
			category_url_list.append([i.text, url])
		except NoSuchElementException:
			print("url为空")
			category_url_list.append([i.text, None])
	return category_url_list


def get_this_level_item_urls(driver) -> List[List]:
	xpath = '//*[@id="gridItemRoot"]/div/div[2]/div/a[2]'  # 获取了图片部份的url
	a_list = driver.find_elements(By.XPATH, xpath)  # .//a[@class="a-link-normal"]/@href')
	item_urls = [[a.text, a.get_attribute("href")] for a in a_list]
	return item_urls


def create_proxy_chrome():
	def create_proxyauth_extension(tunnelhost, tunnelport, proxy_username, proxy_password, scheme='http',
	                               plugin_path=None):
		"""代理认证插件

		args:
			tunnelhost (str): 你的代理地址或者域名（str类型）
			tunnelport (int): 代理端口号（int类型）
			proxy_username (str):用户名（字符串）
			proxy_password (str): 密码 （字符串）
		kwargs:
			scheme (str): 代理方式 默认http
			plugin_path (str): 扩展的绝对路径

		return str -> plugin_path
		"""
		
		if plugin_path is None:
			plugin_path = 'vimm_chrome_proxyauth_plugin.zip'
		
		manifest_json = """
	    {
	        "version": "1.0.0",
	        "manifest_version": 2,
	        "name": "Chrome Proxy",
	        "permissions": [
	            "proxy",
	            "tabs",
	            "unlimitedStorage",
	            "storage",
	            "<all_urls>",
	            "webRequest",
	            "webRequestBlocking"
	        ],
	        "background": {
	            "scripts": ["background.js"]
	        },
	        "minimum_chrome_version":"22.0.0"
	    }
	    """
		
		background_js = string.Template(
			"""
			var config = {
					mode: "fixed_servers",
					rules: {
					singleProxy: {
						scheme: "${scheme}",
						host: "${host}",
						port: parseInt(${port})
					},
					bypassList: ["foobar.com"]
					}
				};

			chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

			function callbackFn(details) {
				return {
					authCredentials: {
						username: "${username}",
						password: "${password}"
					}
				};
			}

			chrome.webRequest.onAuthRequired.addListener(
						callbackFn,
						{urls: ["<all_urls>"]},
						['blocking']
			);
			"""
		).substitute(
			host=tunnelhost,
			port=tunnelport,
			username=proxy_username,
			password=proxy_password,
			scheme=scheme,
		)
		with zipfile.ZipFile(plugin_path, 'w') as zp:
			zp.writestr("manifest.json", manifest_json)
			zp.writestr("background.js", background_js)
		return plugin_path
	
	proxyauth_plugin_path = create_proxyauth_extension(
		tunnelhost="r847.kdltps.com",  # 隧道域名
		tunnelport="15818",  # 端口号
		proxy_username="t18533708977798",  # 用户名
		proxy_password="ukoaa3t8"  # 密码
	)
	
	# chrome_options = webdriver.ChromeOptions()
	# chrome_options.add_extension(proxyauth_plugin_path)
	
	# 每次都创建了一个新的
	options = webdriver.ChromeOptions()
	options.add_argument('--lang=en')
	options.add_argument('--headless')
	
	prefs = {
		"profile.managed_default_content_settings.images": 2  # 不渲染图片，减少内存占用
	}
	options.add_experimental_option("prefs", prefs)
	options.add_extension(proxyauth_plugin_path)
	
	# driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
	driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
	return driver


if __name__ == '__main__':
	options = webdriver.ChromeOptions()
	options.add_argument('--lang=en')
	options.add_argument('--headless')
	
	prefs = {
		"profile.managed_default_content_settings.images": 2  # 不渲染图片，减少内存占用
	}
	options.add_experimental_option("prefs", prefs)
	driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
	
	url = "https://www.amazon.com/Best-Sellers/zgbs/"
	base_url = get_base_url(url)
	driver = webdriver_get(driver, url)
	driver = change_en(driver)  # ，所以不返回任何东西都可以
