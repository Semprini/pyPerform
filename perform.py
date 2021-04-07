import json
import requests

import urllib3
import time

from itertools import islice

from datetime import datetime
from multiprocessing import Process, Lock, Semaphore

import settings

urllib3.disable_warnings()


def dummy_worker(data_chunk, mutex):
    with mutex:
        time.sleep(1)


class Perform():

    def chunk(self, data_list, count_per_chunk):
        data_list = iter(data_list)
        return iter(lambda: tuple(islice(data_list, count_per_chunk)), ())

    def run(self, process_count, worker, data_list):

        chunks = list(self.chunk(data_list, int(len(data_list) / process_count)))

        print("========================================")
        print("    Processes:  {}".format(process_count))
        print("    Total Messages: {}".format(len(data_list)))

        processes = []
        mutexes = []
        mutex = Semaphore(process_count)
        for index in range(0, process_count):
            mutex = Lock()
            mutex.acquire()
            mutexes.append(mutex)

            process = Process(target=worker, args=(chunks[index], mutex), daemon=True)
            processes.append(process)
            process.start()

        start = datetime.now()
        for mutex in mutexes:
            mutex.release()
        print("    Started at {}".format(start))

        done = False
        current_processes = processes
        while not done:
            done = True
            for process in reversed(current_processes):
                if process.is_alive():
                    process.join()
                    done = False
                    continue
                else:
                    current_processes.remove(process)

        end = datetime.now()
        duration = end - start
        dur_ms = (duration.seconds * 1000000) + duration.microseconds
        through = len(data_list) / (dur_ms / 1000000)
        print("    Ended at {}".format(end))
        print("    Duration: {}".format(duration))
        print("    Throughput: {} messages per second".format(through))
        print("========================================\n")

        return (process_count, len(data_list), start, end, duration, through)


class RestPerform(Perform):
    def do_auth(self):
        data = """grant_type=client_credentials&client_id={}&client_secret={}&resource={}""".format(settings.client_id, settings.client_secret, settings.client_resource)

        # Create a new Service charge transaction by calling API
        headers = {
            'Content-type': 'application/x-www-form-urlencoded'
        }
        response = requests.post('https://login.microsoftonline.com/db3d428f-0f97-449a-b683-4df57b0a73c8/oauth2/token', data=data, headers=headers)

        if type(response.content) != bytes:
            json_response = json.loads(response.content)
        else:
            json_response = json.loads(response.content.decode("ascii"))

        if 'access_token' in json_response.keys():
            return "Bearer {}".format(json_response['access_token'])
        else:
            return None

    def post(self, auth, path, data, session=None):

        if auth is None:
            auth = self.do_auth()

        # Create a new Service charge transaction by calling API
        headers = {
            'Content-type': 'application/json',
            'authorization': auth,
            'Host': '{}'.format(settings.host),
        }
        if session is None:
            session = requests.Session()
        url = '{}{}{}'.format(settings.host, settings.base_path, path)
        response = session.post(url, data=data, headers=headers, verify=False)
        if response.status_code != 201:  # (201) Created
            print('HTTP Error {}'.format(response))
            print('    response body: {}'.format(response.content))
            print('Request url: {}'.format(url))
            print('    request headers: {}'.format(headers))
            print("Current time: {}".format(time.time()))

            if response.status_code != 401:
                # print('    request body: {}'.format(data))
                raise Exception("({}) {} \nHeaders: {}".format(response.status_code, response.content, response.headers))
            else:
                time.sleep(2)
                auth = self.do_auth()
                return self.post(auth, path, data, None)

        return session, auth

    def worker(self, data_chunk, mutex):
        with mutex:
            time.sleep(2)
        print("worker done")

    def run(self, process_count, data_list):
        super().run(process_count, self.worker, data_list)


if __name__ == "__main__":
    import random

    data = []
    for i in range(0, 10):
        data.append("{}".format(random.randint(0, 10000)))

    perform = Perform()
    perform.run(5, dummy_worker, data)
