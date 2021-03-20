import json
import requests

import urllib3
import time

from itertools import islice

from datetime import datetime
from multiprocessing import Process

import settings

urllib3.disable_warnings()


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


class Perform():

    def dummy_worker(self, data_chunk):
        time.sleep(1)

    def run(self, process_count, worker, data_list):

        chunks = list(chunk(data_list, int(len(data_list) / process_count)))

        print("========================================\n")
        print("    Processes:  {}".format(process_count))
        print("    Total Messages: {}".format(len(data_list)))

        processes = []
        for process in range(0, process_count):
            processes.append(Process(target=worker, args=(chunks[process],), daemon=True))

        start = datetime.now()
        print("    Started at {}".format(start))
        for process in processes:
            process.start()

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
        through = len(data) / (dur_ms / 1000000)
        print("    Ended at {}".format(end))
        print("    Duration: {}".format(duration))
        print("    Throughput: {} messages per second".format(through))
        print("========================================\n")

        return (process_count, len(data), start, end, duration, through)


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
                return self.post(self.do_auth(), path, data, None)

        return session, auth


if __name__ == "__main__":
    import random

    data = []
    for i in range(0, 10):
        data.append("{}".format(random.randint(0, 10000)))

    perform = Perform()
    perform.run(5, perform.dummy_worker, data)
