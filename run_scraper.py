import argparse
import sys
import time

from image_scraper import ImageScraper


class ImageScraperArgs(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_args()

    def setup_args(self):
        self.add_argument('-urls', type=str, default='urls.txt',
                          help='Path to file with image urls list. '
                               'One url per line')
        self.add_argument('-sl', '--server_list', type=str,
                          help='List of server hosts to distribute scraped '
                               'images to (coma separated).')
        self.add_argument('-i', '--interval', type=int, default=5,
                          help='Set the interval in secs image scraber '
                               'will rerun the task.')
        self.add_argument('-ss', '--stop_server', action='store_true',
                          help='This flag will prevent of running local '
                               'web server (simple Flask app) to handle '
                               'served images from other servers. '
                               'By default if False.')
        self.add_argument('-p', '--port', type=int, default=5000,
                          help='Local server port (if should be run). '
                               '5000 port is used by default')
        self.add_argument('-nd', '--nodistr', action='store_true',
                          help='This flag will disable distribution of '
                               'scraped images to the pointed servers.')
        self.add_argument('-scraped', '--scraped_path', type=str,
                          default='scraped_images',
                          help='Path to save scraped images. Default is '
                               '\'scraped_images\'')
        self.add_argument('-received', '--received_path', type=str,
                          default='received_images',
                          help='Path to save received images. Default is '
                               '\'received_images\'')


if __name__ == '__main__':
    try:
        params = ImageScraperArgs().parse_args(sys.argv[1:])
        image_scraper = ImageScraper(**vars(params))
    except Exception as why:
        print(why)
    else:
        print('start running the tasks...')
        while True:
            image_scraper.run_the_task()
            time.sleep(params.interval)
