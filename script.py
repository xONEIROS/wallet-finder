import os
import hashlib
import requests
import time
from itertools import cycle
from bitcoinlib.keys import PrivateKey
import socket
import socks
from concurrent.futures import ThreadPoolExecutor, as_completed

# تعداد کلیدهای خصوصی که قصد تولید داریم
num_keys = 1000000
num_workers = 10  # تعداد کارگران (تعداد thread ها)

def load_proxies(file_path):
    """بارگذاری پراکسی‌ها از فایل"""
    with open(file_path, 'r') as f:
        proxies = f.read().splitlines()
    return cycle(proxies)

def set_proxy(proxy):
    """تنظیم پراکسی برای درخواست‌ها"""
    proxy = proxy.strip()
    if '@' in proxy:
        user_pass, ip_port = proxy.split('@')
        user, password = user_pass.split(':')
        ip, port = ip_port.split(':')
    else:
        ip, port = proxy.split(':')
        user, password = None, None
    
    socks.set_default_proxy(socks.SOCKS5, ip, int(port), username=user, password=password)
    socket.socket = socks.socksocket

def check_proxy(proxy):
    """بررسی فعال بودن پراکسی"""
    try:
        set_proxy(proxy)
        response = requests.get('http://www.google.com', timeout=5)
        return response.status_code == 200
    except:
        return False

def generate_private_key():
    """تولید یک کلید خصوصی تصادفی"""
    return os.urandom(32)

def private_key_to_wif(private_key):
    """تبدیل کلید خصوصی به فرمت WIF"""
    extended_key = b'\x80' + private_key
    sha256_1 = hashlib.sha256(extended_key).digest()
    sha256_2 = hashlib.sha256(sha256_1).digest()
    checksum = sha256_2[:4]
    wif = extended_key + checksum
    return wif

def private_key_to_address(private_key):
    """تبدیل کلید خصوصی به آدرس عمومی بیت‌کوین"""
    priv = PrivateKey(wif=private_key_to_wif(private_key))
    return priv.address()

def check_balance(address):
    """بررسی موجودی آدرس بیت‌کوین"""
    url = f"https://blockchain.info/rawaddr/{address}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('final_balance', 0)
    else:
        return 0

def save_key_info(index, private_key, address, balance):
    """ذخیره کلید خصوصی و آدرس عمومی در فایل"""
    with open("keys_with_balance.txt", "a") as f:
        f.write(f"{index}: Private Key: {private_key.hex()}, Address: {address}, Balance: {balance}\n")

def process_key(index, proxy):
    private_key = generate_private_key()
    address = private_key_to_address(private_key)
    balance = check_balance(address)
    temp_file = f"temp_key_{index}.txt"
    
    with open(temp_file, "w") as f:
        f.write(f"{index}: Private Key: {private_key.hex()}, Address: {address}, Balance: {balance}\n")
    
    if balance > 0:
        with open("keys_with_balance.txt", "a") as final_file:
            final_file.write(f"{index}: Private Key: {private_key.hex()}, Address: {address}, Balance: {balance}\n")
        print(f"Found address with balance: {address} with balance {balance}")
    else:
        os.remove(temp_file)

def main():
    proxy_cycle = load_proxies("proxy.txt")
    current_proxy = next(proxy_cycle)

    # بررسی و تنظیم پراکسی
    while not check_proxy(current_proxy):
        current_proxy = next(proxy_cycle)
    
    set_proxy(current_proxy)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(process_key, i, current_proxy): i for i in range(num_keys)}
        for future in as_completed(futures):
            index = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"Key {index} generated an exception: {exc}")

            # تغییر پراکسی هر ۲ دقیقه
            if time.time() - start_time > 120:
                current_proxy = next(proxy_cycle)
                while not check_proxy(current_proxy):
                    current_proxy = next(proxy_cycle)
                set_proxy(current_proxy)
                start_time = time.time()
            
            if index % 100 == 0:
                print(f"Checked {index} keys...")

if __name__ == "__main__":
    main()
