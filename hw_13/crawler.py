#!/usr/bin/env python
# coding: utf-8

import aiofiles
import aiofiles.os
import argparse
import asyncio
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import glob
import logging
from lxml import etree
import os
import requests


PAUSE_SEC = 60
DIR_TO_SAVE = 'ycombinator_news'
URL = 'https://news.ycombinator.com'

Article = namedtuple('Article', ['id', 'title', 'url'])


async def waiting_for_upd(outdir, pause):
    while True:
        try:
            await asyncio.wait_for(handle_root_page(outdir), timeout=pause)
        except Exception as exc:
            logging.error(f'Crawler failed: {exc.args}')
        await asyncio.sleep(pause)

async def handle_root_page(outdir):
    response = await download_page(URL, outdir, 'root')
    articles_from_root = parse_root_page(response.content)
    articles = [article
                for article in articles_from_root
                if not is_article_processed(article.id, outdir)]
    
    logging.info(f'New articles count: {len(articles)}')

    tasks = []
    for article in articles:
        tasks.append(asyncio.create_task(handle_article(article, outdir)))
        await asyncio.sleep(1)
    await asyncio.gather(*tasks)

async def download_page(url, dir_to_save, file_name):
    response = await get_response(url)
    filepath = os.path.join(dir_to_save, f'{file_name}')
    with ThreadPoolExecutor() as pool:
        await asyncio.get_running_loop()\
                     .run_in_executor(pool,
                                      save_page_as_file,
                                      str(filepath),
                                      response.content
                                      )
    logging.info(f'{file_name} is saved')
    return response     

async def get_response(url):
    logging.info(f'Download article: {url}')
    
    try:
        async with requests.get(url) as response:
            page = await response.content
            return page
    except requests.exceptions.RequestException:
        logging.error(f'Downloading error: {url}')

async def save_page_as_file(path, content):
    with aiofiles.open(path, 'w') as f:
        await f.write(content)
        
def parse_root_page(content):
    root = etree.HTML(content)
    articles = []
    for article in root.xpath('//tr[@class="athing"]'):
        link = article.xpath('.//a[@class="storylink"]')[0]
        articles.append(Article(id=article.get('id'),
                                title=link.text,
                                url=link.get('href')))
    return articles

def is_article_processed(article_id, outdir):
    article_path = os.path.join(outdir, article_id)
    return not os.path.exists(article_path) and os.path.is_dir(article_path)

async def handle_article(article, outdir):
    logging.debug(f'Article {article.title} is processing, article id: {article.id}')
    article_dir = os.path.join(outdir, article.id)
    
    if not await aiofiles.os.path.exists(article_dir):
        await aiofiles.os.mkdir(article_dir)
    try:
        await asyncio.gather(*[
            download_page(article.url, article_dir, 'article'),
            handle_comments(article.url, article.id, article_dir),
        ])
    except Exception as exc:
        logging.error(f'Article {article.url} processing failed {exc.args}')
    
async def handle_comments(article_url, article_id, article_dir):
    article_full_url = f'{article_url}/item?id={article_id}'
    response = await download_page(article_full_url, article_dir, 'first_layer')
    links = get_links_from_comments(response.content)
    logging.info(f'There are {len(links)} links in the comments of {article_full_url}')
    tasks = []
    for idx, link in enumerate(links):
        tasks.append(asyncio.create_task(download_page(link, article_dir, f'comment_{idx}')))
        await asyncio.sleep(1)
    await asyncio.gather(*tasks)
    
def get_links_from_comments(content):
    root = etree.HTML(content)
    comment_xpath = '//div[@class="comment"]//a[@rel="nofollow"]'
    links_in_comments = [link.get('href')
                        for link in root.xpath(comment_xpath)]
    return links_in_comments


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--outdir', default=DIR_TO_SAVE, type=str, help='Output directory')
    parser.add_argument('-p', '--pause', default=PAUSE_SEC, type=int, help='Root page crawling pause (in seconds)')
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    logging.basicConfig(level=logging.INFO,
                        datefmt='%Y.%m.%d %H:%M:%S',
                        format='[%(asctime)s] %(threadName)s %(levelname)s %(message)s',)

    outdir = os.path(args.outdir)
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    try:
        asyncio.run(waiting_for_upd(outdir, args.pause))

    except asyncio.CancelledError:
        logging.info('Crawler canceled')
    except KeyboardInterrupt:
        logging.info('Crawler stopped')
