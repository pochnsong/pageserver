import time


class IDHelper(object):
    """
    用于生成IDs
    """
    # 64位ID的划分
    WORKER_ID_BITS = 10
    SEQUENCE_BITS = 12

    # 最大取值计算
    MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)  # 2**5-1 0b11111

    # 移位偏移计算
    WORKER_ID_SHIFT = SEQUENCE_BITS
    TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS

    # 序号循环掩码
    SEQUENCE_MASK = -1 ^ (-1 << SEQUENCE_BITS)

    # 北京时间 2020-01-01 0点 时间戳
    TWEPOCH = 1577836800

    def __init__(self, worker_id=1):
        """
        初始化
        :param worker_id: 机器ID
        """
        # sanity check
        if worker_id > self.MAX_WORKER_ID or worker_id < 0:
            raise ValueError('worker_id值越界')

        self.worker_id = worker_id
        self.sequence = 0

        self.last_timestamp = -1  # 上次计算的时间戳

    @classmethod
    def timestamp(cls):
        """
        生成整数时间戳
        :return:int timestamp
        """
        return int(time.time() * 1000)

    def get_id(self):
        """
        获取新ID
        :return:
        """
        timestamp = self.timestamp()

        # 时钟回拨
        if timestamp < self.last_timestamp:
            raise Exception('snowflake clock backwards')

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.SEQUENCE_MASK
            if self.sequence == 0:
                timestamp = self._next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        _timestamp = timestamp - self.TWEPOCH
        new_id = ((_timestamp << self.TIMESTAMP_LEFT_SHIFT) | (self.worker_id << self.WORKER_ID_SHIFT)) | self.sequence
        return new_id

    def _next_millis(self, last_timestamp):
        """
        等到下一毫秒
        """
        timestamp = self.timestamp()
        while timestamp <= last_timestamp:
            timestamp = self.timestamp()
        return timestamp

