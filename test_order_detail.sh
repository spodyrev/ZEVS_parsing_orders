#!/bin/bash
# Тестовый запрос к API деталей заказа

curl 'https://h5api.m.taobao.com/h5/mtop.taobao.order.query.detailv2/1.0/?jsv=2.7.2&appKey=12574478&t='$(date +%s)000'&sign=test&v=1.0&api=mtop.taobao.order.query.detailv2' \
  -H 'content-type: application/x-www-form-urlencoded' \
  --cookie-jar taobao_cookies.txt \
  --data-raw 'data=%7B%22useV2%22%3A%22true%22%2C%22appVersion%22%3A%223.0%22%2C%22archive%22%3Afalse%2C%22appName%22%3A%22tborder%22%2C%22bizOrderId%22%3A%223316188865004009384%22%7D' \
  2>/dev/null | python3 -m json.tool > order_detail_response_example.json 2>/dev/null

echo "Response saved to order_detail_response_example.json"
