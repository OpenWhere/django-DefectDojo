import json
import urllib
from dojo.models import Finding
from selenium import webdriver


class SafetyParser(object):
    def __init__(self, json_output, test):

        # Grab Safety DB for CVE lookup
        url = "https://raw.githubusercontent.com/pyupio/safety-db/master/data/insecure_full.json"
        response = urllib.urlopen(url)
        safety_db = json.loads(response.read())

        tree = self.parse_json(json_output)

        if tree:
            self.items = [data for data in self.get_items(tree, test, safety_db)]
        else:
            self.items = []

    def parse_json(self, json_output):
        json_obj = json.load(json_output)
        tree = {l[4]: {'package': str(l[0]),
                       'affected': str(l[1]),
                       'installed': str(l[2]),
                       'description': str(l[3]),
                       'id': str(l[4])}
                for l in json_obj}
        return tree

    def get_items(self, tree, test, safety_db):
        items = {}

        for key, node in tree.iteritems():
            item = get_item(node, test, safety_db)
            print item
            items[key] = item

        return items.values()


def get_item(item_node, test, safety_db):
    cve = ''.join(a['cve'] for a in safety_db[item_node['package']] if a['id'] == 'pyup.io-' + item_node['id'])
    title = item_node['package'] + " (" + item_node['affected'] + ")"
    if cve:
        title = title + " | " + cve
        cve_sev = get_cve_severity(cve)
        if 0.1 <= float(cve_sev) <= 3.9:
            severity = 'Low'
        elif 4.0 <= float(cve_sev) <= 6.9:
            severity = 'Medium'
        elif 7.0 <= float(cve_sev) <= 8.9:
            severity = 'High'
        else:
            severity = 'Critical'
    else:
        cve = "N/A"
        severity = 'Medium'

    finding = Finding(title=title,
                      test=test,
                      severity=severity,
                      description=item_node['description'] +
                                  "\n Vulnerable Package: " + item_node['package'] +
                                  "\n Installed Version: " + item_node['installed'] +
                                  "\n Vulnerable Versions: " + item_node['affected'] +
                                  "\n CVE: " + cve +
                                  "\n ID: " + item_node['id'],
                      cwe=1035,  # Vulnerable Third Party Component
                      mitigation="No mitigation provided",
                      references="No reference provided",
                      active=False,
                      verified=False,
                      false_p=False,
                      duplicate=False,
                      out_of_scope=False,
                      mitigated=None,
                      impact="No impact provided")

    return finding


def get_cve_severity(cve):
    url = 'https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?name=' + cve
    driver = webdriver.PhantomJS()
    driver.get(url)
    p_element = driver.find_element_by_id(id_='cvss-base-score-cell')
    return p_element.text

