import io
import os

import msgpack
import pytest

from Config import config
from util import Msgpack


class TestMsgpack:
    test_data = {"cmd": "fileGet", "params": {"site": "1Site"}, "utf8": b'\xc3\xa1rv\xc3\xadzt\xc5\xb1r\xc5\x91'.decode("utf8"), "bin": b'p\x81zDhL\xf0O\xd0\xaf', "list": [b'p\x81zDhL\xf0O\xd0\xaf', b'p\x81zDhL\xf0O\xd0\xaf']}

    def testPacking(self):
        assert Msgpack.pack(self.test_data) == b'\x85\xa3cmd\xa7fileGet\xa6params\x81\xa4site\xa51Site\xa4utf8\xad\xc3\xa1rv\xc3\xadzt\xc5\xb1r\xc5\x91\xa3bin\xc4\np\x81zDhL\xf0O\xd0\xaf\xa4list\x92\xc4\np\x81zDhL\xf0O\xd0\xaf\xc4\np\x81zDhL\xf0O\xd0\xaf'
        assert Msgpack.pack(self.test_data, use_bin_type=False) == b'\x85\xa3cmd\xa7fileGet\xa6params\x81\xa4site\xa51Site\xa4utf8\xad\xc3\xa1rv\xc3\xadzt\xc5\xb1r\xc5\x91\xa3bin\xaap\x81zDhL\xf0O\xd0\xaf\xa4list\x92\xaap\x81zDhL\xf0O\xd0\xaf\xaap\x81zDhL\xf0O\xd0\xaf'

    def testUnpackinkg(self):
        assert Msgpack.unpack(Msgpack.pack(self.test_data)) == self.test_data

    @pytest.mark.parametrize("unpacker_class", [msgpack.Unpacker, msgpack.fallback.Unpacker])
    def testUnpacker(self, unpacker_class):
        unpacker = unpacker_class(raw=False)

        data = msgpack.packb(self.test_data, use_bin_type=True)
        data += msgpack.packb(self.test_data, use_bin_type=True)

        messages = []
        for char in data:
            unpacker.feed(bytes([char]))
            for message in unpacker:
                messages.append(message)

        assert len(messages) == 2
        assert messages[0] == self.test_data
        assert messages[0] == messages[1]

    def testStreaming(self):
        bin_data = os.urandom(20)
        f = Msgpack.FilePart("%s/users.json" % config.data_dir, "rb")
        f.read_bytes = 30

        data = {"cmd": "response", "body": f, "bin": bin_data}

        out_buff = io.BytesIO()
        Msgpack.stream(data, out_buff.write)
        out_buff.seek(0)

        data_packb = {
            "cmd": "response",
            "body": open("%s/users.json" % config.data_dir, "rb").read(30),
            "bin": bin_data
        }

        out_buff.seek(0)
        data_unpacked = Msgpack.unpack(out_buff.read())
        assert data_unpacked == data_packb
        assert data_unpacked["cmd"] == "response"
        assert type(data_unpacked["body"]) == bytes

