# filler.py

"""
Given a properly-formatted csv file, post rubric entries to Canvas gradebook.
"""

import os
import sys
import urllib
import time
import urllib.request
import urllib.error
from urllib.request import urlopen
import urllib.parse
import csv

CANVAS_KEY = os.environ["CANVAS_KEY"]
CANVAS_URL = "https://canvas.jmu.edu/"


# https://stackoverflow.com/a/4014164/1449799
def recursive_urlencode(d):
    """URL-encode a multidimensional dictionary.

    >>> data = {'a': 'b&c', 'd': {'e': {'f&g': 'h*i'}}, 'j': 'k'}
    >>> recursive_urlencode(data)
    u'a=b%26c&j=k&d[e][f%26g]=h%2Ai'
    """
    def recursion(d, base=[]):
        pairs = []

        for key, value in d.items():
            new_base = base + [key]
            if hasattr(value, 'values'):
                pairs += recursion(value, new_base)
            else:
                new_pair = None
                if len(new_base) > 1:
                    first = urllib.parse.quote(new_base.pop(0))
                    rest = map(lambda x: urllib.parse.quote(x), new_base)
                    new_pair = "%s[%s]=%s" % (first, ']['.join(
                        rest), urllib.parse.quote(str(value)))
                else:
                    new_pair = "%s=%s" % (urllib.parse.quote(
                        str(key)), urllib.parse.quote(str(value)))
                pairs.append(new_pair)
        return pairs

    return '&'.join(recursion(d))


class GradePoster(object):

    def __init__(self, course_id, assignment_id, key):
        url_string = ("https://canvas.jmu.edu/api/v1/courses/{}"
                      "/assignments/{}/submissions")
        self.url = url_string.format(course_id, assignment_id)
        self.key = key

    def post_grade_update(self, student_id, crit_grade_comments):
        form_data = {"rubric_assessment": {}}
        self.url += "/{}"
        self.url = self.url.format(student_id)
        for crit in crit_grade_comments:
            form_data['rubric_assessment'][crit] = {
                "points": crit_grade_comments[crit]["points"]
            }
            if "comment" in crit_grade_comments[crit] and \
                    len(crit_grade_comments[crit]["comment"]) > 0:
                form_data['rubric_assessment'][crit]["comments"] = \
                    crit_grade_comments[crit]["comment"]

        form_data = recursive_urlencode(form_data)
        data = str.encode(form_data)
        header = {"Authorization": "Bearer {}".format(self.key)}
        request = urllib.request.Request(self.url, data, headers=header,
                                         method="PUT")
        attempt_count = 0

        while attempt_count < 4:
            try:
                return urlopen(request)
            except urllib.error.URLError as e:
                print("URL ERROR, trying again " + str(e) + e.reason)
                time.sleep(.5)
                attempt_count += 1
        print("Giving up.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("USAGE: python filler.py graded-with-rubric.csv course_id \
                assignment_id")
        sys.exit(1)
    COURSE_ID = sys.argv[2]
    ASSIGNMENT_ID = sys.argv[3]

    # Test Student for CS 101 F18
    gp = GradePoster(COURSE_ID, ASSIGNMENT_ID, CANVAS_KEY)
    with open(sys.argv[1], encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sid = row["SID"]
            crit_grade_comments = {}
            for item in filter(lambda x: x != "SID", row):
                crit_grade_comments[item] = {"points": row[item]}
            response = gp.post_grade_update(sid, crit_grade_comments)
            print(response.read())
