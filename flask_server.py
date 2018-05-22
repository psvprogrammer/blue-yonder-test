import os

from flask import Flask, Response
from flask import request


app = Flask(__name__)
target_dir = os.path.join(os.curdir, 'served_images')


@app.route('/add/image/<image_name>', methods=['POST'])
def add_image(image_name):
    if request.method == 'POST':
        try:
            with open(os.path.join(target_dir, image_name), 'wb') as image:
                image.write(request.data)
                return Response(status=200)
        except Exception as why:
            print('Error: {}. Skipping file storage.'.format(why))
            return Response(status=500)
    return Response(status=400)


if __name__ == '__main__':
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    app.run()
