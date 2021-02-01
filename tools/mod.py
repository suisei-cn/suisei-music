import xxhash

class Music(object):
    __slots__ = [
        'datetime',
        'video_type',
        'video_id',
        'clip_start',
        'clip_end',
        'status',
        'title',
        'artist',
        'performer',
        'hash',
    ]

    def __init__(self, item):
        self.datetime = item['datetime']
        self.video_type = item['video_type']
        self.video_id = item['video_id']
        self.clip_start = item['clip_start']
        self.clip_end = item['clip_end']
        self.status = item['status']
        self.title = item['title']
        self.artist = item['artist']
        self.performer = item['performer']

        self.hash = xxhash.xxh64(''.join([
            self.video_type,
            self.video_id,
            self.clip_start,
            self.clip_end,
            self.title,
            self.artist,
            self.performer
        ]), seed=0x9f88f860).hexdigest()

    def __hash__(self):
        return int(self.hash, 16)

    def __repr__(self):
        return f'Music(id={self.video_id}, title={self.title}, key={self.hash})'