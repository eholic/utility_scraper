# utility-scraper
## Quick Start

```python
from denki_kakeibo import DenkiKakeibo
with DenkiKakeibo('username', 'password') as dk:
    # 最新の時間データを取得
    json_dict = dk.fetch_usage_30Min()
    print(json_dict)

    # 前日の時間データを取得
    json_dict = dk.fetch_usage_30Min(previous=1)
    print(json_dict)

```

## License
This code is released under the MIT License, see ![LICENSE](LICENSE)
