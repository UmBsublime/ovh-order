import logging
import click

import ovh
from order import ServerOrder

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s %(message)s')
logger = logging.getLogger(__file__)

#CLIENT = ovh.Client()

@click.group()
@click.option('--debug/--no-debug', '-d', default=False)
@click.option('--config', '-C', default='~/.ovh.conf')
@click.pass_context
def cli(ctx, debug, config):
    ctx.obj['DEBUG'] = debug
    ctx.obj['CLIENT'] = ovh.Client(config_file=config)

    logger.setLevel(logging.INFO)
    #logger.info("Info level")
    #print("Info level")
    if ctx.obj['DEBUG']:
        logger.setLevel(logging.DEBUG)
        logger.debug("debug level")

@cli.command(help='Generate a new cart _OR_ list the contents of a cart')
@click.option('--cart', '-c',
              default=None,
              envvar='OVH_CART_ID',
              help="If one is supplied will list the contents of the cart")
@click.pass_context
def cart(ctx, cart):
    if cart:
        order = ServerOrder(ctx.obj['CLIENT'], cart_id=cart)
        order.show_cart()
    else:
        order = ServerOrder(ctx.obj['CLIENT'])
        click.echo('export OVH_CART_ID={}'.format(order.cart_id))


@cli.command()
@click.argument('server',
                required=True)
@click.argument('cart',
                envvar='OVH_CART_ID',
                required=True)
@click.option('--duration', '-d',
              default='P1M',
              help='Duration of the rental in ISO-XXX format')
@click.option('--pricing-mode', '-p',
              default='default',
              help='Pricing mode')
@click.option('--quantity', '-q',
              default=1,
              help='Quantity of servers to add')
@click.pass_context
def add(ctx, cart, server, duration, pricing_mode, quantity):
    """ Add a server to a cart

    \b
    CART:   Cart ID of the order you are working on
    SERVER: Server code of the server you would like to add to the cart

    """
    order = ServerOrder(ctx.obj['CLIENT'], cart_id=cart)
    order.add_server_to_order(server, duration, pricing_mode, quantity)

@cli.command(help="List servers available for purchase")
@click.pass_context
def servers(ctx):
    s = ServerOrder(ctx.obj['CLIENT'])
    s.show_server_list()

@cli.command()
@click.argument('item',
                required=True)
@click.argument('cart',
                envvar='OVH_CART_ID',
                required=True)
@click.pass_context
def config(ctx, cart, item):
    """ Get available configuration options for a server

    \b
    CART: Cart ID of the order you are working on
    ITEM: Item ID of the item you want to get options from
    """

    s = ServerOrder(ctx.obj['CLIENT'], cart_id=cart)
    s.show_item_required_config(item)

@cli.command()
@click.argument('item',
                required=True)
@click.argument('label',
                required=True)
@click.argument('value',
                required=True)
@click.argument('cart',
                envvar='OVH_CART_ID',
                required=True)
@click.pass_context
def config_add(ctx, cart, item, label, value):
    """ Set a configuration parameter on a cart item

    \b
    CART:  Cart ID of the order you are working on
    ITEM:  Item ID of the item you want to get options from
    LABEL: Label of the parameter you want to set
    VALUE: Value of the parameter you want to set
    """
    s = ServerOrder(ctx.obj['CLIENT'], cart_id=cart)
    s.add_item_config(item, label, value)

@cli.command()
@click.argument('item',
                required=True)
@click.argument('cart',
                envvar='OVH_CART_ID',
                required=True)
@click.pass_context
def config_get(ctx, cart, item):
    """ Get currently configured options for a server

    \b
    CART: Cart ID of the order you are working on
    ITEM: Item ID of the item you want to get options from
    """
    s = ServerOrder(ctx.obj['CLIENT'], cart_id=cart)
    s.show_item_config(item)

@cli.command()
@click.argument('cart',
                envvar='OVH_CART_ID',
                required=True)
@click.option('--waive-retractation-period', '-w',
              default=False)
@click.pass_context
def checkout(ctx, cart, waive_retractation_period):
    """ Assign and checkout cart

    \b
    CART: Cart ID you want to checkout
    """
    s = ServerOrder(ctx.obj['CLIENT'], cart_id=cart)
    s.assign_cart()
    url = s.checkout_cart(waive_retractation_period)
    click.echo(url)
    click.echo('unset OVH_CART_ID')

if __name__ == "__main__":
    cli(obj={})
