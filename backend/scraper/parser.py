"""
Парсер данных о заказах с Taobao
Извлечение нужной информации из HTML/JSON
"""

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from loguru import logger
from datetime import datetime


class TaobaoParser:
    """
    Парсер данных Taobao
    """
    
    @staticmethod
    def parse_order_from_json(api_data: Dict, order_id: str) -> Optional[Dict]:
        """
        Парсит данные заказа из JSON ответа API
        
        Args:
            api_data: Полный JSON объект data.data из API ответа
            order_id: ID заказа для парсинга
            
        Returns:
            Dict: Нормализованные данные заказа
        """
        try:
            # Извлекаем данные из разных объектов по order_id
            shop_info = api_data.get(f"shopInfo_{order_id}", {}).get("fields", {})
            order_payment = api_data.get(f"orderPayment_{order_id}", {}).get("fields", {})
            order_deliver = api_data.get(f"orderDeliverTime_{order_id}", {}).get("fields", {})
            
            # Ищем orderItemInfo (может быть несколько товаров в заказе)
            items = []
            item_keys = [k for k in api_data.keys() if k.startswith(f"orderItemInfo_{order_id}_")]
            
            for item_key in item_keys:
                item_data = api_data.get(item_key, {}).get("fields", {}).get("item", {})
                if item_data:
                    items.append(item_data)
            
            # Если нет items, пытаемся найти основной item
            if not items:
                main_item = api_data.get(f"orderItemInfo_{order_id}_{order_id}", {}).get("fields", {}).get("item", {})
                if main_item:
                    items.append(main_item)
            
            # Извлекаем tracking number (если есть)
            tracking_number = None
            # TODO: Найти где в API хранится tracking number
            # Обычно появляется после отправки товара
            
            # Формируем описание из первого товара
            description = ""
            total_quantity = 0
            product_url = None
            product_image_url = None
            
            if items:
                first_item = items[0]
                title = first_item.get("title", "")
                sku_text = first_item.get("skuText", "")
                description = f"{title}"
                if sku_text:
                    description += f" | {sku_text.strip()}"
                
                # Извлекаем URL товара
                item_url = first_item.get("itemUrl", "")
                if item_url:
                    # Убеждаемся что это полный URL
                    if item_url.startswith("//"):
                        product_url = f"https:{item_url}"
                    elif not item_url.startswith("http"):
                        product_url = f"https://{item_url}"
                    else:
                        product_url = item_url
                
                # Извлекаем URL изображения
                pic_url = first_item.get("pic", "")
                if pic_url:
                    # Убеждаемся что это полный URL
                    if pic_url.startswith("//"):
                        product_image_url = f"https:{pic_url}"
                    elif not pic_url.startswith("http"):
                        product_image_url = f"https://{pic_url}"
                    else:
                        product_image_url = pic_url
                
                # Считаем общее количество
                for item in items:
                    qty_str = item.get("quantity", "1")
                    try:
                        total_quantity += int(qty_str)
                    except ValueError:
                        total_quantity += 1
            
            # Извлекаем цену
            actual_fee = order_payment.get("actualFee", {}).get("value", "￥0.00")
            price_str = actual_fee.replace("￥", "").replace("¥", "").replace(",", "").strip()
            total_price = float(price_str) if price_str else 0.0
            
            # Извлекаем статус и дату
            trade_title = shop_info.get("tradeTitle", "")  # "买家已付款"
            deliver_title = order_deliver.get("title", "")  # "待发货"
            create_time_str = shop_info.get("createTime", "")  # "2026-08-06 23:11:36"
            
            # Определяем статус заказа
            status = TaobaoParser._normalize_status_from_titles(trade_title, deliver_title)
            
            order = {
                "order_id": order_id,
                "tracking_number": tracking_number,
                "status": status,
                "description": description[:500] if description else "Без описания",
                "product_url": product_url,
                "product_image_url": product_image_url,
                "items_count": total_quantity,
                "total_price": total_price,
                "currency": "CNY",
                "order_date": TaobaoParser._parse_date(create_time_str),
                "raw_data": {
                    "shop_info": shop_info,
                    "payment": order_payment,
                    "delivery": order_deliver,
                    "items": items
                }
            }
            
            logger.debug(f"Распарсен заказ: {order['order_id']} - {status}")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка парсинга заказа {order_id}: {e}")
            return None
    
    @staticmethod
    def parse_order_from_html(html: str) -> Optional[Dict]:
        """
        Парсит данные заказа из HTML страницы
        
        Args:
            html: HTML код страницы заказа
            
        Returns:
            Dict: Нормализованные данные заказа
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # TODO: Адаптировать под реальную структуру HTML Taobao
            # Это пример, нужно будет найти правильные селекторы
            
            order = {
                "order_id": TaobaoParser._extract_text(soup, ".order-id"),
                "tracking_number": TaobaoParser._extract_text(soup, ".tracking-number"),
                "status": TaobaoParser._normalize_status(
                    TaobaoParser._extract_text(soup, ".order-status")
                ),
                "description": TaobaoParser._extract_text(soup, ".item-title"),
                "items_count": 1,
                "total_price": TaobaoParser._extract_price(soup, ".order-price"),
                "currency": "CNY",
                "order_date": None,
                "raw_data": {"html_length": len(html)}
            }
            
            return order
            
        except Exception as e:
            logger.error(f"Ошибка парсинга заказа из HTML: {e}")
            return None
    
    @staticmethod
    def parse_orders_list(data: Dict) -> List[Dict]:
        """
        Парсит список заказов из JSON ответа Taobao API
        
        Args:
            data: JSON объект со списком заказов (формат mtop.taobao.order.queryboughtlistv2)
            
        Returns:
            List[Dict]: Список нормализованных заказов
        """
        orders = []
        
        try:
            # Структура ответа: data -> data -> [объекты с разными тегами]
            api_data = data.get("data", {}).get("data", {})
            
            if not api_data:
                logger.warning("Пустой ответ API")
                return orders
            
            # Собираем все order_id из объектов shopInfo
            order_ids = set()
            for key, value in api_data.items():
                if isinstance(value, dict) and value.get("tag") == "shopInfo":
                    order_id = value.get("id")
                    if order_id:
                        order_ids.add(order_id)
            
            logger.info(f"Найдено {len(order_ids)} заказов в ответе API")
            
            # Парсим каждый заказ
            for order_id in order_ids:
                order = TaobaoParser.parse_order_from_json(api_data, order_id)
                if order:
                    orders.append(order)
            
            logger.info(f"Успешно распарсено {len(orders)} заказов")
            
        except Exception as e:
            logger.error(f"Ошибка парсинга списка заказов: {e}")
        
        return orders
    
    @staticmethod
    def parse_tracking_from_detail(detail_data: Dict) -> Optional[str]:
        """
        Извлекает трек-номер из детального ответа API заказа
        
        Args:
            detail_data: JSON ответ от mtop.taobao.order.query.detailv2
            
        Returns:
            str: Трек-номер или None
        """
        try:
            # Путь к трек-номеру: data.data.logisticsPackages.fields.packageInfos[0].mailNo
            api_data = detail_data.get("data", {}).get("data", {})
            
            # Ищем объект logisticsPackages
            logistics_packages = api_data.get("logisticsPackages", {})
            
            if not logistics_packages:
                logger.debug("logisticsPackages не найден в ответе API")
                return None
            
            # Извлекаем packageInfos
            fields = logistics_packages.get("fields", {})
            package_infos = fields.get("packageInfos", [])
            
            if not package_infos or len(package_infos) == 0:
                logger.debug("packageInfos пуст")
                return None
            
            # Берем первую посылку (обычно заказ содержит одну посылку)
            first_package = package_infos[0]
            mail_no = first_package.get("mailNo", "")
            
            if mail_no:
                logger.info(f"✅ Найден трек-номер: {mail_no}")
                return mail_no
            else:
                logger.debug("mailNo пуст в первой посылке")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка парсинга трек-номера: {e}")
            return None
    
    @staticmethod
    def _normalize_status_from_titles(trade_title: str, deliver_title: str) -> str:
        """
        Нормализует статус заказа на основе tradeTitle и deliverTitle
        
        Args:
            trade_title: Статус сделки (например, "买家已付款")
            deliver_title: Статус доставки (например, "待发货")
            
        Returns:
            str: Нормализованный статус
        """
        if not trade_title and not deliver_title:
            return "created"
        
        # Маппинг статусов на основе реальных данных Taobao
        status_map = {
            # Trade Title статусы
            "买家已付款": "paid",  # Buyer paid
            "等待买家付款": "created",  # Waiting for buyer payment
            "交易成功": "delivered",  # Trade successful
            "交易关闭": "cancelled",  # Trade closed
            
            # Delivery Title статусы
            "待发货": "paid",  # Waiting for shipment
            "待收货": "shipped",  # Waiting for delivery
            "已完成": "delivered",  # Completed
            "已签收": "delivered",  # Signed for
            "运输中": "shipped",  # In transit
        }
        
        # Сначала проверяем delivery статус (более приоритетный)
        for key, value in status_map.items():
            if key in deliver_title:
                return value
        
        # Затем проверяем trade статус
        for key, value in status_map.items():
            if key in trade_title:
                return value
        
        logger.warning(f"Неизвестный статус: trade='{trade_title}', deliver='{deliver_title}'")
        return "created"
    
    @staticmethod
    def _normalize_status(status: Optional[str]) -> str:
        """
        Нормализует статус заказа (старый метод для совместимости)
        
        Args:
            status: Статус из Taobao
            
        Returns:
            str: Нормализованный статус
        """
        if not status:
            return "created"
        
        status = status.lower()
        
        # Маппинг статусов Taobao на наши статусы
        status_map = {
            "待付款": "created",
            "wait_buyer_pay": "created",
            "已付款": "paid",
            "买家已付款": "paid",
            "wait_seller_send_goods": "paid",
            "待发货": "paid",
            "已发货": "shipped",
            "wait_buyer_confirm_goods": "shipped",
            "待收货": "shipped",
            "运输中": "shipped",
            "已收货": "delivered",
            "已完成": "delivered",
            "trade_finished": "delivered",
            "已取消": "cancelled",
            "trade_closed": "cancelled",
        }
        
        for key, value in status_map.items():
            if key in status:
                return value
        
        logger.warning(f"Неизвестный статус: {status}")
        return "created"
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """
        Парсит дату из строки
        
        Args:
            date_str: Строка с датой
            
        Returns:
            datetime: Объект даты
        """
        if not date_str:
            return None
        
        try:
            # Попытка разных форматов даты
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Не удалось распарсить дату: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка парсинга даты: {e}")
            return None
    
    @staticmethod
    def _extract_text(soup: BeautifulSoup, selector: str) -> Optional[str]:
        """
        Извлекает текст по CSS селектору
        """
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
        return None
    
    @staticmethod
    def _extract_price(soup: BeautifulSoup, selector: str) -> Optional[float]:
        """
        Извлекает цену и конвертирует в float
        """
        text = TaobaoParser._extract_text(soup, selector)
        if text:
            try:
                # Удаляем символы валюты и пробелы
                price_str = text.replace("¥", "").replace("￥", "").replace(",", "").strip()
                return float(price_str)
            except ValueError:
                pass
        return None


# Пример использования
if __name__ == "__main__":
    # Пример JSON данных (тестовые)
    test_data = {
        "orderId": "TB123456789",
        "status": "已发货",
        "title": "Xiaomi Phone",
        "payment": 299.99,
        "createTime": "2024-01-15 10:30:00"
    }
    
    parser = TaobaoParser()
    order = parser.parse_order_from_json(test_data)
    
    if order:
        print("Распарсенный заказ:")
        for key, value in order.items():
            if key != "raw_data":
                print(f"  {key}: {value}")
