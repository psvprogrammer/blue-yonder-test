# Image scraper
*This code is a part of test task for [Blue-yonder company.](https://www.blue-yonder.com)*

# Task description
> Given a plaintext file containing URLs, one per line, e.g.:
> 
> http://mywebserver.com/images/271947.jpg
> http://mywebserver.com/images/24174.jpg
> http://somewebsrv.com/img/992147.jpg

> Write a script that takes this plaintext file as an argument and downloads all images, storing them on the local hard disk. Approach the problem as you would any task > in a normal day’s work. Imagine this code will be used in important live systems, modified later on by other developers, and so on.
> Please use the Python programming language for your solution. We prefer to receive your code in GitHub or a similar repository.
> In a deployment scenario this script needs to be deployed to multiple Debian machines, scheduled to run every five minutes. The downloaded images should be served via > http on each server.
> Provide an example deployment or instructions with your solution.

# Before running
To start using this script you need to know the list of other servers where to serve scraped data.

To simplify the task I suggest using [**```ngrok```**](https://ngrok.com/) to provide access to local web server from outside. Simple prefered usage:
```
.ngrok http 5000
```
This will provide public url that can be lately used with *-sl* key to run_scraper.py

# Solution overview
The image scraper by default will run local web server to handle receiving data from other servers.
This is a simple Flask server with one particular end-point at *'/add/image/<image_name>'* that will handle POST request with data to store them localy then.
Optionaly, you can prevent of starting web server by adding *-ss*:
```
python run_scraper.py -ss
```
Image scraper will automaticaly rerun the task with interval. Default interval is 5 sec. 
You can specify another period with *-i 60* flag.

For full help info read "Help & Description" section.

# Usage

## Requirements
To start using the script install the requirements first. It require only *aiohttp* and *flask* libraries:
```
pip install -r requirements.txt
```

## Basic example
```
python run_scraper.py
```
This will run local web server and will serve scraped images to itself just to demostrate that it works.

To run scraper with specified server list you should run:
```
python run_scraper.py -sl http://263e4972.ngrok.io,http://263e4955.ngrok.io
```
> **Note:**  
> Multiple server public urls should be coma separated with no spaces.

To prevent sendind scraped data to the servers you can specify the *-nd* flag:
```
python run_scraper.py -nd
```
This will only collect data from given urls.txt.

## Help & Description
Image scraper object and it's logic itself described at **```image_scraper.py```**.
To run the scraper you should run **```run_scraper.py```**.
Theare is a help provided with *run_scraper* that describes all possible parameters that can be used. To get help:
```
python run_scraper.py -h
```