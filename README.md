# utility_scraper
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

## Quick Start

### DenkiKakeibo
```python
from utility_scraper.denki_kakeibo import DenkiKakeibo

with DenkiKakeibo('username', 'password') as dk:
    # 最新の時間データを取得
    json_dict = dk.fetch_usage_30Min()
    print(json_dict)
    # {'day': '2017/11/02', 'value': '0.10, ...

    # 前日の時間データを取得
    json_dict = dk.fetch_usage_30Min(previous=1)
    print(json_dict)
    # {'day': '2017/11/01', 'value': '0.10, ...

    # 月別のデータを取得
    json_dict = dk.fetch_usage_monthly()
    print(json_dict)
    # {'monthly': [{'month': '2015/11', 'value': {'day': '', 'kWh': '', 'payment': ''}}, 
```

### MyTokyoGas
```python
from utility_scraper.my_tokyo_gas import MyTokyoGas

with MyTokyoGas('username', 'password') as tg:
    # 月別のデータを取得
    json_dict = tg.fetch_usage_monthly()
    print(json_dict)
    # {'monthly': [{'month': '2014/11', 'payment': ''}, ...
```


## License
This code is released under the MIT License, see ![LICENSE](LICENSE)
