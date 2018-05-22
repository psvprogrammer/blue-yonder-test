import asyncio
import aiohttp

import logging
import os
import threading
import time

import flask_server

from os import walk


log = logging.getLogger()
log.setLevel(logging.DEBUG)

SERVERS = (
    # list of server urls to serve scraped images to
    'http://127.0.0.1:5000/add/image',
)


class ImageScraper:
    def __init__(self, urls=None,
                 server_list=SERVERS,
                 stop_server=False, port=5000, nodistr=False,
                 scraped_path='scraped_images',
                 received_path='received_images', **kwargs):
        """
        This class represents an object that will help you to scrap data
        from given list of urls
        :param urls: str. Path to a file with urls to scrap
        :param server_list: str (optional). The urls of machines
        where we should serve scraped images.
        Multiple hosta names should be coma separated.
        :param stop_server: bool (optional). This will prevent of starting
        local web server to receive data from other servers.
        By default if False.
        :param port: int (optional). Port of local web server to start on.
        :param nodistr: bool (optional). This flag will prevent auto serving
        scraped data to the servers. By default if False.
        :param scraped_path: str (optional). Path where scraped data
        should be stored to. By default it 'scraped_images' in current folder.
        :param received_path: str (optional). Path where received data
        should be stored to. By default it 'received_images' in current folder.
        :param kwargs: (optional). Other possible named parameters.
        """

        self._urls_path = urls
        self._serve = not nodistr
        self._received_path = received_path
        self._scraped_path = scraped_path

        self._server_thread = threading.Thread(
            target=self._start_server, args=(port,)
        )
        if not stop_server:
            flask_server.target_dir = self._received_path
            # starting local web server to receive images
            # from other servers
            self._check_path_exists(received_path)
            print('starting local web server to receive images...')
            try:
                self._server_thread.start()
            except Exception as why:
                print("Failed to start local web server! {}".format(why))
            else:
                print('Done!')

        self._urls = None
        self._len = None
        self._fetched_imgs = None
        self._served_img_count = None
        self._serve_img_len = None

        if isinstance(server_list, str):
            try:
                self._servers = set(server_list.split(','))
            except Exception as why:
                log.error("Error parsing server list: {}".format(why))
                if not nodistr:
                    raise
        elif server_list is None:
            # trying to take default module value
            self._servers = SERVERS

        try:
            self._parse_urls_from_file()
        except Exception as why:
            log.exception("Unhandled exception "
                          "on parsing data! {}".format(why))

    def _start_server(self, port=5000):
        flask_server.app.run(port=port)

    def _check_path_exists(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as why:
                log.error("Error creating target directory {}".format(why))
                raise

    def _print_progress_bar(self, iteration, total, prefix='', suffix='',
                            decimals=1, length=100, fill='█'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(
            100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
        # Print New Line on Complete
        if iteration == total:
            print()

    def _get_image_name(self, url):
        """
        This method help us to get 100% unique name
        for the file we are trying to download based on url
        :param url: str. Url we are trying to fetch.
        :return: str. Unique name for file.
        """
        filenames = next(walk(self._scraped_path))[-1]
        try:
            name = url.rsplit('/', 1)[-1]
        except IndexError:
            name = str(time.time())
        if name in filenames:
            if '.' in name:
                name, ext = name.rsplit('.', 1)
                name = name + '_' + str(time.time()) + '.' + ext
            else:
                name += '_' + str(time.time())
        return os.path.join(self._scraped_path, name)

    async def _get_img(self, session, url):
        image_name = self._get_image_name(url)
        with aiohttp.Timeout(10):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        img = await response.read()
                        try:
                            with open(image_name, 'wb') as f:
                                f.write(img)
                        except Exception as why:
                            log.error("Error storing fetched file from url "
                                      "{}: {}. "
                                      "Skipping this url.".format(url, why))
                        else:
                            self._fetched_imgs.append(image_name)
                            self._print_progress_bar(
                                len(self._fetched_imgs), len(self))
                    else:
                        print("Can't fetch image "
                              "{}: {}".format(url, response))
            except Exception as why:
                log.error("Error fetching url '{}': '{}'... "
                          "Skipping this url.".format(url[:50], str(why)[:100]))
                self._len -= 1

    async def _post_image(self, session, url, image_path):
        try:
            with open(image_path, 'rb') as image:
                try:
                    url += '/' + image_path.rsplit('/')[-1]
                    async with session.post(url, data=image) as response:
                        if response.status == 200:
                            self._print_progress_bar(self._served_img_count+1,
                                                     self._serve_img_len)
                        else:
                            log.error("Error posting {} to {}: {}"
                                      .format(image_path, url, response))
                except Exception as why_post_error:
                    log.error("Error sending {} to {}: {}"
                              .format(image_path, url, why_post_error))
        except Exception as why:
            log.error("Error serving '{}' to url '{}': {}. "
                      "Skipping this serve.".format(image_path, url, why))
        self._served_img_count += 1

    def _parse_urls_from_file(self):
        if isinstance(self._urls_path, str):
            if os.path.exists(self._urls_path):
                try:
                    with open(self._urls_path) as file:
                        self._urls = {url.replace(os.linesep, '')
                                      for url in file.readlines() if
                                      url.strip() != ''}
                except OSError as why:
                    log.error("Error trying to read file "
                              "with urls: {}".format(why))
            else:
                log.error("File expected under data string doesn't exist! "
                          "Aborting scraping")
                return
        else:
            log.error("Data is not an appropriate type! Aborting scraping")
            raise

        if self._urls:
            self._len = len(self._urls)
        else:
            self._len = 0

    def get_images(self):
        if self._urls:
            self._check_path_exists(self._scraped_path)
            self._fetched_imgs = []
            loop = asyncio.get_event_loop()
            with aiohttp.ClientSession(loop=loop) as session:
                tasks = [self._get_img(session, url) for url in self._urls]
                print('Start image scraping...')
                loop.run_until_complete(asyncio.wait(tasks))
                print("Finished scraping")
        else:
            log.error("The list of urls is empty!")

    def serve_images(self):
        if self._servers and len(self._servers) > 0:
            if self._fetched_imgs and len(self._fetched_imgs) > 0:
                self._served_img_count = 0
                self._serve_img_len = len(self._servers) * len(self._fetched_imgs)
                loop = asyncio.get_event_loop()
                with aiohttp.ClientSession(loop=loop) as session:
                    tasks = [self._post_image(session, url, image_path)
                             for url in self._servers
                             for image_path in self._fetched_imgs]
                    print('Started image serving...')
                    loop.run_until_complete(asyncio.wait(tasks))
                    print("Finished image serving.")
            else:
                print("No images to serve!")
        else:
            log.error("Server list is empty!")

    def run_the_task(self):
        self._parse_urls_from_file()
        self.get_images()
        if self._serve:
            self.serve_images()

    def __len__(self):
        if self._len:
            return self._len
        else:
            if self._urls:
                return len(self._urls)
            else:
                return 0
