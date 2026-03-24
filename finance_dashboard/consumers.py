import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TerminalConsumer(AsyncWebsocketConsumer):
    """ Tổng đài đẩy dữ liệu PnL, Equity, Exposure thời gian thực """
    async def connect(self):
        self.account_id = self.scope['url_route']['kwargs']['account_id']
        self.group_name = f'terminal_{self.account_id}'

        # Gia nhập nhóm để nhận tin
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Nhận dữ liệu từ Celery/System và bắn lên React
    async def send_metrics(self, event):
        await self.send(text_data=json.dumps(event['data']))

class RadarConsumer(AsyncWebsocketConsumer):
    """ Tổng đài đẩy tín hiệu Radar/AlphaSignal mới nhất """
    async def connect(self):
        await self.channel_layer.group_add('radar_group', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('radar_group', self.channel_name)

    async def new_signal(self, event):
        await self.send(text_data=json.dumps(event['data']))