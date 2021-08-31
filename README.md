# PixivDaily (Python)

The used to be the backend server script for the Telegram channel "[Pixiv Daily](https://t.me/pixiv_daily)". This script stopped working around the end of 2019. A newer, currently-in-use version of this script has been rewritten in Rust and can be found at [pixivdaily-rust](https://github.com/k4yt3x/pixivdaily-rust).

This script was written when I was less competent at writing Python. **Before you read the code, be warned that it's far from pretty or efficient.**

## Usage

```console
usage: pixiv_daily_rankings.py [-h] [-s] [-n] [-v]

optional arguments:
  -h, --help     show this help message and exit

Controls:
  -s, --serve    Start feeding images to channels
  -n, --now      Post immediately for once and enter normal cycle
  -v, --version  Prints program version and exit
```
