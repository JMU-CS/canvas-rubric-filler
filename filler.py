# # filler.py

# # Import the Canvas class
# from canvasapi import Canvas

import os
CANVAS_KEY = os.environ["CANVAS_KEY"]
CANVAS_URL = "https://canvas.jmu.edu/"

# if __name__ == "__main__":    

#     # Initialize a new Canvas object
#     canvas = Canvas(CANVAS_URL, CANVAS_KEY)
#     # print(dir(canvas))
#     # print(canvas.get_user(5480485))
#     course = canvas.get_course(1584732)
#     # for r in course.get_rubrics():
#     #     print(r)
#     print(dir(course.get_rubric(687653)))
#     assg = course.get_assignment(9810070)
#     submission = assg.get_submission(5533888)


import sys
import urllib
import time
# import urllib2
import urllib.request
import urllib.error
from urllib.request import urlopen
import urllib.parse

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
        for crit in crit_grade_comments:
            form_data['rubric_assessment'][crit]={
                "points": crit_grade_comments[crit]["pts"],
                "comments": crit_grade_comments[crit]["comment"]
            }
            # print(crit, crit_grade_comments[crit]["pts"], crit_grade_comments[crit]["comment"])
        # rubric_assessment = 'rubric_assessment[{}][points]'.format(crit)
        # form_data[rubric_assessment] = pts
        # grade_key = 'grade_data[{}][posted_grade]'.format(student_id)
        # form_data[grade_key] = grade

        # # if comment != "":
        # #     comment_key = 'grade_data[{}][text_comment]'.format(student_id)
        # #     form_data[comment_key] = comment

        form_data = recursive_urlencode(form_data)
        # print(form_data)
        data = str.encode(form_data)
        # data = urllib.parse.urlencode(form_data).encode("utf-8")
        # data = urllib.parse.urlencode(form_data)
        # print(data)
        header = {"Authorization": "Bearer {}".format(self.key)}
        # print(header)
        request = urllib.request.Request(self.url, data, headers=header)
        # print(request.get_full_url())
        # print(request.header_items())
        attempt_count = 0
        # print(request)
        while attempt_count < 4:
            try:
                return urlopen(request)
            except urllib.error.URLError as e:
                print("URL ERROR, trying again " + str(e) + e.reason)
                time.sleep(.5)
                attempt_count += 1
        print("Giving up.")


if __name__ == "__main__":
    COURSE_ID = "1584732"
    ASSIGNMENT_ID = "9810070"
    student_id = "5587357"
    gp = GradePoster(COURSE_ID, ASSIGNMENT_ID, CANVAS_KEY)
    crit_grade_comments = {
        "criterion__5412": {
            "pts": 2,
            "comment": ""
        },
        "criterion__3145": {
            "pts": 2,
            "comment": ""
        },
        "criterion__6838": {
            "pts": 0.5,
            "comment": ""
        },
        "criterion__4455": {
            "pts": 2,
            "comment": ""
        },
        "criterion__1269": {
            "pts": 2,
            "comment": ""
        },
        "criterion__8517": {
            "pts": 0.5,
            "comment": ""
        }
    }

    gp.post_grade_update(student_id, crit_grade_comments)
    # response = gp.post_grade_update(student_id, crit_grade_comments)
    # print response.read()
