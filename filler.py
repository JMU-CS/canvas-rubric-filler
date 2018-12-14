# filler.py

import os
CANVAS_KEY = os.environ["CANVAS_KEY"]
CANVAS_URL = "https://canvas.jmu.edu/"

import sys
import urllib
import time
import urllib.request
import urllib.error
from urllib.request import urlopen
import urllib.parse

import csv

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
        form_data = {"rubric_assessment":{}}
        self.url += "/{}"
        self.url = self.url.format(student_id)
        print(self.url)
        for crit in crit_grade_comments:
            form_data['rubric_assessment'][crit]={
                "points": crit_grade_comments[crit]["points"]
            }
            if "comment" in crit_grade_comments[crit] and len(crit_grade_comments[crit]["comment"]) > 0:
                form_data['rubric_assessment'][crit]["comments"]: crit_grade_comments[crit]["comment"]

        form_data = recursive_urlencode(form_data)
        # print(form_data)
        data = str.encode(form_data)
        print(data)
        header = {"Authorization": "Bearer {}".format(self.key)}
        request = urllib.request.Request(self.url, data, headers=header, method="PUT")
        attempt_count = 0

        # "/api/v1/courses/:course_id/rubrics/:id"
        # request = urllib.request.Request(
        #     CANVAS_URL+"api/v1/courses/"+COURSE_ID+"/assignments/9810058/submissions/5533888?include[]=rubric_assessment", headers=header)
        while attempt_count < 4:
            try:
                return urlopen(request)
            except urllib.error.URLError as e:
                print("URL ERROR, trying again " + str(e) + e.reason)
                time.sleep(.5)
                attempt_count += 1
        print("Giving up.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: python filler.py graded-with-rubric.csv")
        sys.exit(1)
    COURSE_ID = "1584732"
    # ASSIGNMENT_ID = "9810070" #demo?
    ASSIGNMENT_ID = "9810058"  # lab07
    student_id = "5587357" #Test Student for CS 101
    gp = GradePoster(COURSE_ID, ASSIGNMENT_ID, CANVAS_KEY)
    with open(sys.argv[1], encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row)
            sid = row["SID"]
            crit_grade_comments = {}
            for item in filter(lambda x: x != "SID", row):
                crit_grade_comments[item] = {"points": row[item]}
            response = gp.post_grade_update(student_id, crit_grade_comments)
            print(response.read())

    # crit_grade_comments = {
    #     # these can come from the rubric page.  e.g. https://canvas.jmu.edu/courses/1584732/rubrics/687658
    #     # inspect the table to get the criteria ids
    #     # $(".criterion:not(.blank, #criterion_1)").map((i,e)=>e.id.substring("criterion_".length))
    #     # "415008_7565": { 
    #     #     "points": 1,
    #     #     "comment": ""
    #     # },
    #     # "415008_2320": {
    #     #     "points": 0,
    #     # },
    #     "415008_1553": {
    #         "points": 2,
    #     },
    #     "415008_261": {
    #         "points": 4,
    #     }
    # }

    # response = gp.post_grade_update(student_id, crit_grade_comments)
    # print(response.read())
