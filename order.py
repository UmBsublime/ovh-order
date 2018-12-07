#!/usr/bin/env python3
import logging

import ovh
from prettytable import PrettyTable

from pprint import pprint

logger = logging.getLogger(__name__)

class ServerOrder:
    def __init__(self, api_client, ovh_subsidiary='US', cart_id=None):
        self.client = api_client
        self.ovh_subsidiary = ovh_subsidiary
        self.cart_id = cart_id
        if not self.cart_id:
            self.cart_id = self.create_cart()
            logger.debug("Generated cart with ID: {}".format(self.cart_id))
        self.products = self.client.get('/order/catalog/formatted/dedicated', ovhSubsidiary=self.ovh_subsidiary)

    def show_server_list(self):
        t = PrettyTable(field_names=['Code', 'DC', 'CPU', 'MEM', 'Disks', 'Price'])
        t.align = 'l'
        t.sortby = 'Code'
        for server in self.products['products']:
            row = []
            row.append(server['code'])
            row.append(', '.join(server['datacenters']))
            row.append('{} {}Mhz'.format(server['specifications']['cpu']['model'], server['specifications']['cpu']['frequency']))
            row.append(server['specifications']['memory']['type'])
            disk_info = ''
            for disk in server['specifications']['disks']:
                disk_info += '{} x {}mb {}'.format(disk['number'],
                                                   disk['size'],
                                                   disk['type'])
            row.append(disk_info)
            row.append(server['prices']['default']['renew']['text'])
            t.add_row(row)
        print(t)

    def add_server_to_order(self, product_code, duration='P1M', pricing_mode='default', quantity=1):
        r = self.client.post('/order/cart/{}/dedicated'.format(self.cart_id),
                             duration=duration,
                             planCode=product_code,
                             pricingMode=pricing_mode,
                             quantity=quantity)
        return r['itemId']

    def remove_server_from_cart(self, item_id):
        self.client.delete('/order/cart/{}/item/{}'.format(self.cart_id, item_id))

    def clear_cart(self):
        item_ids = self.client.get('/order/cart/{}'.format(self.cart_id))['items']
        for item_id in item_ids:
            self.remove_server_from_cart(item_id)

    def delete_cart(self):
        self.client.delete('/order/cart/{}'.format(self.cart_id))

    def get_carts(self):
        r = self.client.get('/order/cart/')
        pprint(r)

    def create_cart(self):
        r = self.client.post('/order/cart', ovhSubsidiary=self.ovh_subsidiary)
        return r['cartId']

    def show_cart(self):
        t = PrettyTable(field_names=['ItemID', 'Product Code', 'Duration', 'Price', 'Quantity'])
        t.align = 'l'
        t.sortby = 'ItemID'
        item_ids = self.client.get('/order/cart/{}'.format(self.cart_id))['items']

        for item_id in item_ids:
            row = []
            item = self.get_cart_item(item_id)
            row.append(item['itemId'])
            row.append(item['settings']['planCode'])
            row.append(item['duration'])
            row.append(item['prices'][0]['price']['text'])
            row.append(item['settings']['quantity'])
            t.add_row(row)
        print(t)

    def get_cart_item(self, item_id):
        r = self.client.get('/order/cart/{}/item/{}'.format(self.cart_id, item_id))
        return r

    def show_item_required_config(self, item_id):
        config_options= self.client.get('/order/cart/{}/item/{}/requiredConfiguration'.format(self.cart_id, item_id))
        fields = ['allowedValues', 'fields', 'label', 'required', 'type']
        t = PrettyTable(field_names=fields)
        for option in config_options:
            row = []
            for field in fields:
                row.append(option.get(field, ''))
            t.add_row(row)

        print(t)

    def show_item_config(self, item):
        configs = self.client.get('/order/cart/{}/item/{}/configuration'.format(self.cart_id, item))
        t = PrettyTable(field_names=['Id', 'Label', 'Value'])
        for config in configs:

            r = self.client.get('/order/cart/{}/item/{}/configuration/{}'.format(self.cart_id, item, config))
            t.add_row([r['id'], r['label'], r['value']])
        print(t)

    def add_item_config(self, item, label, value ):
        self.client.post('/order/cart/{}/item/{}/configuration'.format(self.cart_id, item),
                         label=label,
                         value=value)

    def assign_cart(self):
        self.client.post('/order/cart/{}/assign'.format(self.cart_id))

    def checkout_cart(self, waive_retractation_period=False):
        r = self.client.post('/order/cart/{}/checkout'.format(self.cart_id), waiveRetractationPeriod=waive_retractation_period)
        return r['url']


def banner(text, fill='*'):
    template = "{fill_80}\n{fill_1}{text:^78}{fill_1}\n{fill_80}"
    print(template.format(fill_80=fill*80, fill_1=fill, text=text))


if __name__ == "__main__":

    # Create our Client object
    banner("* OVH Client created *")

    client = ovh.Client()

    # Create a ServerOrder object
    banner("* Server order created *")
    order = ServerOrder(client)

    # List available servers
    banner("* List of available servers for order *")
    order.show_server_list()

    # Add a server to the order
    banner("* Adding GAM-1 server to our order *")
    itemid = order.add_server_to_order('GAM-1')

    # Show the content of the cart
    banner("* Current cart content *")
    order.show_cart()

    # Show required configuration options for the newly added server
    banner("* Configuration options for GAM-1 *")
    order.show_item_required_config(itemid)

    # Add the proper configuration options
    banner("* Adding required configuration for GAM-1 *")
    order.add_item_config(itemid, 'dedicated_datacenter', 'vin')
    order.add_item_config(itemid, 'dedicated_os', 'none_64.en')

    # Show the current config for the server
    banner("* Showing the current configuration for GAM-1 *")
    order.show_item_config(itemid)

    # Assign the cart
    banner("* Assigning cart *")
    order.assign_cart()

    # Checkout the order
    banner("* Checking out order *")
    url = order.checkout_cart()
    print("Order URL: {}".format(url))

    # BONUS: You can clear the cart with
    #order.clear_cart()
