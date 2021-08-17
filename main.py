import sys
import argparse

import pandas as pd
from art import text2art

from core import Account

def get_args():
    description = text2art('crawler-instagram')
        
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f'\n{description}\n',
        epilog="Please support me :)",
        prog='crawler_instagram'
    )
    parser.add_argument( 
        '-U',
        '--username',
        help = "username profile scraper.",
        type = str,
        required = True
    )
    parser.add_argument( 
        '-P',
        '--password',
        help = "password profile scraper.",
        type = str,
        required = True
    )
    parser.add_argument( 
        '-L',
        help = """List of targets to crawl.
        These files must have one column username.
        If there are no two columns in a row, it will be removed from the target list.""",
        type = argparse.FileType('r', encoding='utf-8'),
        dest='users_file',
        required = True
    )
    return parser.parse_args()

def validate_users_file(args) -> list:
    df = pd.read_csv(args.users_file.name, encoding='utf-8', dtype=str)
    if not 'username' in df.columns:
        raise Exception(f"There is not column <username> in {args.users_file.name}.")
    targets = list()
    for _, row in df.dropna().iterrows():
        targets.append(row.username)
    return targets

def login_CLI(username, password) -> Account:
    account = Account(username=username, password=password)
    ans_login = account.login()
    if ans_login.get('authenticated') != True:
        raise Exception('username or password is invalid.')
    print('Logged in successfully.')
    return account



DEBUG = False
if __name__ == '__main__':
    args = get_args()
    if DEBUG:
        from secret_data import TRUE_PROFILES
        username = TRUE_PROFILES[0]['username'] #args['username']
        password = TRUE_PROFILES[0]['password'] #args['password']
    else:
        username = args.username
        password = args.password

    targets = validate_users_file(args)
    account = login_CLI(username, password)
    account.init_csv()
    for target in targets:
        account.get_posts(target)
