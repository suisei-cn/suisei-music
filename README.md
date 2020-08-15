# Suisei Music

A project collecting all music performed by [Hoshimati Suisei](https://www.hololive.tv/portfolio/items/345947)

## Data

[suisei-music.csv](suisei-music.csv) contains useful information:

- `date`: The date when the video is released or the livestream is started
- `video_type`: `YOUTUBE` for [Youtube](https://www.youtube.com/) and `BILIBILI` for [bilibili](https://www.bilibili.com/)
- `video_id`: Video id for website
- `clip_start`: The timing when clip start in seconds with 0.2s padding
- `clip_end`: The timing when clip end in seconds with 0.2s padding
- `status`: Bitflags, 0x1 acappella, 0x2 corrupt, 0x4 silent/clipped due to youtube policy, 0x8 member-only
- `title`: The title of the song
- `artist`: The original artist of the song
- `performer`: The performer of the song

## Tools

**workflow.py** is a helper script that:

1. check music metadata
2. download the audio source with the best quality
3. clip into separate audio file without lossy compression

## LICENSE

The license for [suisei-music.csv](suisei-music.csv) is CC0. A human-readable version of the license is available [here](https://creativecommons.org/publicdomain/zero/1.0/), which also directs to the full license. The license for other files in this repository are MIT.

The MIT License

Copyright (c) 2020 Daniel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
