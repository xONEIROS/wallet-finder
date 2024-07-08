# خب در اینترنت و مخصوصا اینستا زیاد دیدین که طرف میاد یک ساکریپت رو ران میکنه و بعد از چند دقیقه یک بیت کوین پیدا میکنه :))

## حالا اینکه یک عده میرن پول میدن میخرن و اینارو ول کنیم در اصل باید بدونیم چنین چیزی نشدنی است ، یا احتمال اون اونقدر کمه که میگیم نشدنی !
### حالا بیاید فرض کنیم میشه خیلی راحت یک سری پراویت کی و پابلیک کی تولید کردن و یک ربات هم داشت که اتوماتیک بیاید تمامی پابلیک کی و پرایویت کی های ساخته شده رو باهم تست کنه و هر کدوم موجودی داشت رو براتون یک جا ذخیره کنه!

#### حتی این ربات اونقدر هوشمنده که برای جلوگیری از بن شدن از پراکسی استفاده میکنه و برای بالا بردن سرعت خودش از multiprocessing  کمک میگیره!

**با همه این تفاسیر میتونیم چنین رباتی به شکل زیر داشته باشیم و بصورت بخش بخش شما میتونید همه اجزا اونو ببینید**

قبل از شروع به مطالعه باید بدونید این مقاله صرفا برای آموزش و درک مسئله ساخته شده و هیچ استفاده دیگیری از دید ارائه دهنده ندارد.

### بخش‌های اسکریپت و توضیحات

#### تولید کلید خصوصی تصادفی:
تابع `generate_private_key` از `os.urandom` برای تولید یه کلید خصوصی ۳۲ بایتی استفاده می‌کنه.

#### تبدیل کلید خصوصی به فرمت WIF:
تابع `private_key_to_wif` کلید خصوصی رو به فرمت Wallet Import Format (WIF) تبدیل می‌کنه.

#### تبدیل کلید خصوصی به آدرس عمومی بیت‌کوین:
تابع `private_key_to_address` کلید خصوصی رو به آدرس عمومی بیت‌کوین تبدیل می‌کنه.

#### بررسی موجودی آدرس:
تابع `check_balance` با استفاده از API سرویس Blockchain.info موجودی آدرس رو بررسی می‌کنه.

#### ذخیره کلید خصوصی و آدرس عمومی:
تابع `save_key_info` اطلاعات کلید خصوصی، آدرس عمومی و موجودی رو در فایل `keys_with_balance.txt` ذخیره می‌کنه.

#### شروع جست و جو پیدا کردن والت:
در تابع `main`، تعداد مشخصی کلید خصوصی تولید می‌شه و آدرس‌های عمومی متناظر با اون‌ها بررسی می‌شن. اگه آدرس دارای موجودی غیرصفر باشه، کلید خصوصی و آدرس عمومی در فایل ذخیره می‌شن.

#### برای پراکسی‌ها هم
اول باید کتابخونه `requests[socks]` رو نصب کنی:
```sh
pip install requests[socks]
```
بعد فایل `proxy.txt` رو به صورت زیر ایجاد کن و پراکسی‌های خودتو داخلش ذخیره کن:
```sh
user1:pass1@ip1:port1
user2:pass2@ip2:port2
...
```

# حالا در زیر تمامی بخش‌های اجرایی رو تک تک با هم بررسی می‌کنیم تا ببینیم چی میشه در اینجور فرضیه‌ها

### 1. بارگذاری پراکسی‌ها و تنظیم اونا

```python
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
    proxy رو پاکسازی کن
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
```
- `load_proxies`: این تابع پراکسی‌ها رو از یه فایل بارگذاری می‌کنه.
- `set_proxy`: این تابع پراکسی فعلی رو تنظیم می‌کنه.
- `check_proxy`: این تابع فعال بودن پراکسی رو بررسی می‌کنه.

### 2. تولید کلید خصوصی و تبدیل اون به آدرس عمومی

```python
def generate_private_key():
    """تولید یه کلید خصوصی تصادفی"""
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
```
- `generate_private_key`: این تابع یه کلید خصوصی تصادفی تولید می‌کنه.
- `private_key_to_wif`: این تابع کلید خصوصی رو به فرمت WIF تبدیل می‌کنه.
- `private_key_to_address`: این تابع کلید خصوصی رو به آدرس عمومی بیت‌کوین تبدیل می‌کنه.

### 3. بررسی موجودی آدرس و ذخیره اطلاعات

```python
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
```
- `check_balance`: این تابع موجودی آدرس بیت‌کوین رو بررسی می‌کنه.
- `save_key_info`: این تابع اطلاعات کلید خصوصی، آدرس عمومی و موجودی رو در فایل ذخیره می‌کنه.

### 4. پردازش کلید و حذف فایل‌های غیرضروری

```python
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
```
- `process_key`: این تابع کلید خصوصی رو تولید، موجودی رو بررسی و فایل‌های غیرضروری رو حذف می‌کنه.

### 5. اجرای اصلی اسکریپت

```python
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
```
- `main`: این تابع اصلی اسکریپته که پراکسی‌ها رو مدیریت، کلیدها رو تولید و نتایج رو پردازش می‌کنه.

### مراحل استفاده در محیط SSH لینوکس

1. **نصب پایتون**
   ```sh
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **نصب پیش‌نیازها**
   ```sh
   pip3 install requests[socks] bitcoinlib
   ```

3. **دانلود فایل از گیت هاب**
   ```sh
   git clone https://github.com/xOneiros/wallet-finder.git
   cd wallet-finder
   ```

4. **جای‌گذاری مواردی که لازم است**
   - فایل `proxy.txt` رو با محتوای پراکسی‌های خودت ایجاد کن.
   - اطمینان حاصل کن که فایل `proxy.txt` توی همون دایرکتوری اسکریپت قرار داره.

5. **لینک‌های API مورد نیاز**
   - برای بررسی موجودی آدرس بیت‌کوین، از API سایت [blockchain.info](https://blockchain.info/rawaddr/) استفاده می‌شه.


### . جای‌گذاری مواردی که لازم است

فایل `proxy.txt` رو با محتوای پراکسی‌های خودت ایجاد کن. هر خط باید شامل یه پراکسی به فرمت زیر باشه:
```
user:pass@ip:port
```

### 5. اجرای اسکریپت

برای اجرای اسکریپت، از دستور زیر استفاده کن:
```sh
python3 script.py
```

### توضیحات اضافی

- اسکریپت از API سایت [blockchain.info](https://blockchain.info/rawaddr/) برای بررسی موجودی آدرس‌های بیت‌کوین استفاده می‌کنه.
- در صورت پیدا کردن آدرس با موجودی غیرصفر، کلید خصوصی و آدرس عمومی در فایل `keys_with_balance.txt` ذخیره می‌شن.

### هشدار

این اسکریپت فقط برای اهداف آموزشی ارائه شده و استفاده از اون برای حملات واقعی به شدت نامناسب و غیرقانونیه.