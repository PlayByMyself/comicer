import asyncio
import json
from collections import OrderedDict
from typing import List

import click
import toml

from comicer.config import CONFIG
from comicer.spider import MoxMoeSpider, Spider

spider_dict = OrderedDict({"mox": MoxMoeSpider()})


@click.command(name="start", no_args_is_help=True)
@click.option("-a", "--all", is_flag=True)
@click.argument(
    "sources",
    nargs=-1,
    type=click.Choice(list(spider_dict.keys())),
)
def source_start(all: bool, sources: List[str]):
    spider_list: List[Spider] = []
    if all:
        spider_list = list(spider_dict.values())
    else:
        spider_list = [spider_dict[source_name] for source_name in sources]
    if spider_list:
        asyncio.run(run_all_spider(spider_list))


async def run_all_spider(spider_list: List[Spider]):
    await asyncio.gather(*[spider.start() for spider in spider_list])


@click.command(name="list")
def source_list():
    for key in spider_dict:
        click.echo(
            key
            + "("
            + str(spider_dict[key].source.start_url.scheme)
            + "://"
            + str(spider_dict[key].source.start_url.host)
            + ")"
        )


@click.group()
def source():
    pass


@click.group()
@click.version_option()
def main():
    pass


@click.command()
def config():
    click.echo(toml.dumps(json.loads(CONFIG.json())))


source.add_command(source_start)
source.add_command(source_list)

main.add_command(source)
main.add_command(config)
