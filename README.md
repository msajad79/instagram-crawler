# instagram-crawler
Instagram crawler.
Crawling the basic information and posts of the Instagram account.
## Installation
1. first step clone repository
    ```bash
    git clone https://github.com/msajad79/instagram-crawler.git
    ```
2. Install libraries
    ```bash
    pip install requirements.txt
    ```
3. Create a TXT (or CSV) file and enter the username whose data you want to crawl.
Must be the name of username column.

    | username      |
    |:-------------:|
    |instagram      |
    |cristiano      |
    |selenagomez    |
    |leomessi       |
    |...            |
4. Finally, run the program as follows.
    ```bash
    python main.py -U <username> -P <password> -L <path file> 
    ```
# TODO:
- [ ] handle 429 status code
- [ ] User interface design
