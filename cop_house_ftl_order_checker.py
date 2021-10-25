import requests, json, random, csv, time
from threading import Thread, Lock
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def string_builder(string, type):
    if type == "success":
        return '['+str(datetime.now()).split(' ')[1]+'] [FTLCHECKER] ' + bcolors.OKGREEN + string + bcolors.ENDC
    elif type == "warning":
        return '['+str(datetime.now()).split(' ')[1]+'] [FTLCHECKER] ' + bcolors.WARNING + string + bcolors.ENDC
    else:
        return '['+str(datetime.now()).split(' ')[1]+'] [FTLCHECKER] ' + bcolors.FAIL + string + bcolors.ENDC


def load_proxies():

    proxies_vector = []

    with open("proxies.txt", 'r') as fp:
        all_proxies = fp.read().split('\n')

        if all_proxies == ['']:
            print(string_builder('No proxies found, running localhost..', 'warning'))
        else:
            for line in all_proxies:
                try:
                    proxy_parts = line.split(':')
                    ip, port, user, password = proxy_parts[0], proxy_parts[1], proxy_parts[2], proxy_parts[3]
                    tempProxy = {
                        'http': f'http://{user}:{password}@{ip}:{port}',
                        'https': f'http://{user}:{password}@{ip}:{port}'
                    }
                    proxies_vector.append(tempProxy)
                except:
                    pass

            print(string_builder('Loaded ' + str(len(proxies_vector)) + ' proxies.', 'warning'))
    
    return proxies_vector


class ftl_order_checker(Thread):

    headers = {
        'authority': 'footlocker.narvar.com',
        'method': 'GET',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }

    writeMutex = Lock()
    webhookMutex = Lock()
    delay = 2
    webhook = "https://discord.com/api/webhooks/821454214240272384/oQtjciYP6sAvQgc2NorwSVrp9decsk75bBZj_eIQy57G6aiv-KR-A8xShhLNOlmvIPEe"
    url = "https://footlocker.narvar.com/footlocker/tracking/uk-mail?order_number="

    proxies_vector = load_proxies()


    def __init__(self, order_number):
        Thread.__init__(self)
        self.order_number = order_number
        self.session = requests.session()

    def pick_proxy(self):
        index = random.randrange(len(ftl_order_checker.proxies_vector))
        self.proxy_to_use = ftl_order_checker.proxies_vector[index]
        self.session.proxies = self.proxy_to_use
        ftl_order_checker.proxies_vector.remove(self.proxy_to_use)
    
    def check_status(self):
        
        self.link = f"https://footlocker.narvar.com/tracking/itemvisibility/v1/footlocker/orders/{self.order_number}?order_number={self.order_number}&tracking_url=https://footlocker.narvar.com/footlocker/tracking/uk-mail?order_number={self.order_number}"
        
        print(string_builder("[ORDER][" + self.order_number + '] CHECKING', 'warning'))
        try:
            if len(ftl_order_checker.proxies_vector) != 0:
                self.pick_proxy()
            self.r = self.session.get(self.link, headers = ftl_order_checker.headers)
            while self.r.status_code != 200:
                print(string_builder("[ORDER][" + self.order_number + '] BANNED', 'failed'))
                time.sleep(2)
                self.check_status()
            else:
                self.data_order = json.loads(self.r.text)
        except:
            print(string_builder("[ORDER][" + self.order_number + '] FAILED', 'failed'))
    
    def get_data(self):

        #print(self.data_order)

        try:
            self.status = self.data_order['status']
            if self.status == 'SUCCESS':
                self.temp_json = self.data_order['order_info']['order_items'][0]
                self.item_name = self.temp_json['name']
                self.SKU = self.temp_json['sku']
                self.size = self.SKU[12] + self.SKU[13] + self.SKU[14]
                self.item_image = 'http://' + str(self.temp_json['item_image']).replace('//','')
                self.fulfillment_status = self.temp_json['fulfillment_status']

                #possibili altri status?
                if self.fulfillment_status == 'PROCESSING':
                    print(string_builder("[ORDER][" + self.order_number + '] PROCESSING', 'warning'))
                    self.complete_task()
                elif self.fulfillment_status == 'SHIPPED' or 'RETURNED':
                    print(string_builder("[ORDER][" + self.order_number + '] SHIPPED', 'success'))

                    self.temp_ship_json = self.data_order['order_info']['shipments'][0]
                    self.carrier = self.temp_ship_json['carrier']
                    self.tracking = self.temp_ship_json['tracking_number']

                    try:
                        self.tracking_url = str(self.data_order).split("None, 'tracking_url': '")[1].split("'")[0]
                    except:
                        print(string_builder("[ORDER][" + self.order_number + '] TRACKING NOT AVAILABLE', 'warning'))
                    
                    self.complete_task()
            
            else:
                print(string_builder("[ORDER][" + self.order_number + '] CANCELLED ?', 'failed'))
                self.complete_task()

        except Exception:
            print(string_builder("[ORDER][" + self.order_number + '] FAILED', 'failed'))

    def complete_task(self):
        self.write_csv()
        self.send_webhook()
        print(string_builder("[ORDER][" + self.order_number + '] SAVED', 'success'))    


    def write_csv(self):
        ftl_order_checker.writeMutex.acquire()
        with open('orderstatus.csv', 'a', newline = '') as file:
            succesWriter = csv.writer(file)
            if self.status == 'SUCCESS':
                if self.fulfillment_status == 'PROCESSING':
                    succesWriter.writerow([self.order_number, self.item_name, self.size, self.fulfillment_status])
                else:
                    succesWriter.writerow([self.order_number, self.item_name, self.size, self.fulfillment_status, self.carrier, self.tracking, self.tracking_url])
            else:
                succesWriter.writerow([self.order_number, '', 'CANCELLED'])
        ftl_order_checker.writeMutex.release()

    def send_webhook(self):
        ftl_order_checker.webhookMutex.acquire()

        temp_order = '||' + self.order_number + '||'
    
        if self.status == 'SUCCESS':
            temp_name = self.item_name
            temp_size = self.size
            embed = DiscordEmbed(title = 'FOOTLOCKER ORDER CHECKER', color = 808080)
            embed.add_embed_field(name = 'ORDER', value = temp_order, inline = False)
            embed.add_embed_field(name = 'PRODUCT', value = temp_name, inline = True)
            embed.add_embed_field(name = 'SIZE', value = temp_size, inline = True)

            if self.fulfillment_status == 'PROCESSING':
                embed.add_embed_field(name = 'STATUS', value = 'PROCESSING', inline = False)
            else:
                embed.add_embed_field(name = 'STATUS', value = 'SHIPPED', inline = False)
                temp_carrier = self.carrier
                temp_tracking = '||' + self.tracking + '||'
                temp_link = '||' + self.tracking_url + '||'
                embed.add_embed_field(name = 'CARRIER', value = temp_carrier, inline = True)
                embed.add_embed_field(name = 'TRACKING', value = temp_tracking, inline = True)
                if self.tracking_url != '':
                    embed.add_embed_field(name = 'LINK', value = temp_link, inline = False)

                
            embed.set_thumbnail(url = self.item_image)
        else:
            embed = DiscordEmbed(title = 'FOOTLOCKER ORDER CHECKER', color = 808080)
            embed = DiscordEmbed(title = temp_order, color = 808080)
            embed.add_embed_field(name = 'STATUS', value = 'F IN CHAT PLEASE', inline = False)
        #aggiungere logo footer
        embed.set_footer(text = 'COP HOUSE FTL ORDER CHECKER')

        webhook = DiscordWebhook(url = ftl_order_checker.webhook)
        webhook.add_embed(embed)

        try:
            webhook.execute()
        except:
            print(string_builder("[ORDER][" + self.order_number + '] WEBHOOK ERROR', 'failed'))

        ftl_order_checker.webhookMutex.release()
                

        
    def run(self):
        self.check_status()
        self.get_data()



