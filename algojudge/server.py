from algojudge import config
from algojudge.judge import Judge, Submission
from socketserver import StreamRequestHandler, ThreadingTCPServer

import hmac
import json
import logging
import struct


class JudgeHandler(StreamRequestHandler):
    def handle(self):
        logging.debug(f'Connected to {self.client_address}')

        data = self.read_data()
        if data is None:
            logging.debug('Failed to read data :(')
            return

        self.do_request(data)

    def do_request(self, data):
        match data['header']:
            case 'submit':
                self.do_submit(data)

    def do_submit(self, data):
        self.judge = Judge()

        # Authenticate the client's key. Also this check alone clearly isn't
        # gonna cut it in terms of security but it's a start.
        if not hmac.compare_digest(data['access-token'], config.JUDGE_ACCESS_TOKEN):
            return

        submission = Submission(
            id=data['id'],
            problem_code=data['problem-code'],
            language=data['language'],
            source=data['source'].encode('utf-8', errors='replace'),
            time_limit=data['time-limit'],
            memory_limit=data['memory-limit']
        )

        self.send_data({'header': 'judging-begin'})

        for header, verdict in self.judge.judge(submission):
            self.send_data({'header': header, **verdict})

        self.send_data({'header': 'judging-end'})

    def read_data(self):
        packed_msglen = self.rfile.read(4)
        if not packed_msglen:
            return None

        msglen = struct.unpack('!I', packed_msglen)[0]

        data = self.rfile.read(msglen)
        if not data:
            return None

        return json.loads(data)

    def send_data(self, obj):
        data = json.dumps(obj).encode('utf-8')
        self.wfile.write(struct.pack('!I', len(data)) + data)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    import os

    if os.geteuid() != 0:
        print('You must have root permissions to run this judge!')
        raise SystemExit(1)

    from algojudge.comparators import load_comparators
    from algojudge.runners import load_runners

    load_comparators()
    load_runners()

    # Just a hack to get rid of the "Address is already in use" message.
    ThreadingTCPServer.allow_reuse_address = True

    with ThreadingTCPServer(config.SERVER_ADDRESS, JudgeHandler) as server:
        server.serve_forever()
