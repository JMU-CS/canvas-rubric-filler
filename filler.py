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
import argparse
import canvasapi
import functools
import json
import requests

CANVAS_KEY = os.getenv("CANVAS_KEY")
CANVAS_URL = os.getenv("CANVAS_URL")
SID = "SID"
HTTP_SUCCESS = 200


def get_rubric_info(course_id, assignment_id):
    canvas = canvasapi.Canvas(CANVAS_URL, CANVAS_KEY)
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    criteria_id = [[criterion["description"], criterion["points"],
                    criterion["id"]] for criterion in assignment.rubric]
    return criteria_id


def csv_expected_format(criteria_id):
    return [SID]+[elem[2] for elem in criteria_id]


class GradePoster(object):

    def __init__(self, course_id, assignment_id, key):
        self.course_id = course_id
        self.assignment_id = assignment_id
        self.key = key

    def post_grade_update(self, student_id, crit_grade_comments):
        url_string = ("{}api/v1/courses/{}"
                      "/assignments/{}/submissions")
        url = url_string.format(CANVAS_URL, self.course_id, self.assignment_id)
        form_data = {"rubric_assessment": {}}
        url += "/{}"
        url = url.format(student_id)
        for crit in crit_grade_comments:
            form_data['rubric_assessment'][crit] = {
                "points": crit_grade_comments[crit]["points"]
            }
            if "comment" in crit_grade_comments[crit] and \
                    len(crit_grade_comments[crit]["comment"]) > 0:
                form_data['rubric_assessment'][crit]["comments"] = \
                    crit_grade_comments[crit]["comment"]
        data = str.encode(json.dumps(form_data))
        header = {"Authorization": "Bearer {}".format(self.key)}
        return requests.put(url, data, headers=header)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    if CANVAS_KEY is None:
        parser.add_argument(
            "canvas_key", help="your canvas account token. see: https://canvas.instructure.com/doc/api/file.oauth.html#manual-token-generation")

    if CANVAS_URL is None:
        parser.add_argument(
            "canvas_url", help="the URL of your canvas instance, e.g. \
                                https://canvas.jmu.edu/")

    parser.add_argument("course", help="canvas course id")
    parser.add_argument("assignment", help="canvas assignment id")
    parser.add_argument(
        "csv", help="csv file with header: SID, crit1_id, crit2_id...",
        nargs="?", default=None)
    parser.add_argument("--verbose", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()
    if CANVAS_KEY is None:
        if args.canvas_key is None:
            print("your canvas key must be defined either in you environment \
                   as CANVAS_KEY or as the first command line argument")
            sys.exit(1)

        CANVAS_KEY = args.canvas_key

    if CANVAS_URL is None:
        if args.canvas_url is None:
            print("your canvas url must be defined either in you environment \
                   as CANVAS_URL or as the second command line argument")
            sys.exit(1)

        CANVAS_URL = args.canvas_url

    COURSE_ID = int(args.course)
    ASSIGNMENT_ID = int(args.assignment)

    criteria = get_rubric_info(COURSE_ID, ASSIGNMENT_ID)
    expected = csv_expected_format(criteria)

    VERBOSE = args.verbose
    if args.csv is None:
        message = "given that the assignment with id: {} has a rubric with \
criteria: {}\nthe csv is expected to have exactly the {} following columns (\
and header):\n{}".format(ASSIGNMENT_ID, criteria, len(expected),
                         ",".join(expected))
        print(message)
        sys.exit(0)
    
    successes = []
    failures = []

    gp = GradePoster(COURSE_ID, ASSIGNMENT_ID, CANVAS_KEY)
    with open(args.csv, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fields = reader.fieldnames
        if not set(expected) == set(fields):
            message = "invalid csv headers. expected: {}, but got: {}".format(
                expected, actual)
            print(message)
            sys.exit(0)

        successes = {}
        failures = {}
        for row in reader:
            sid = row[SID]
            crit_grade_comments = {}
            for item in filter(lambda x: x != SID, row):
                crit_grade_comments[item] = {"points": row[item]}
            response = gp.post_grade_update(sid, crit_grade_comments)
            if response.ok:
                if VERBOSE:
                    print(response)
                successes[sid] = crit_grade_comments
            else:  # failure case
                crit_grade_comments["error_message"] = response
                failures[sid] = crit_grade_comments

        success_count = len(successes.keys())
        suffix = "es"
        if success_count > 0:
            if success_count == 1:
                suffix = ""
            print(success_count, "success" + suffix)

        failure_count = len(failures.keys())
        suffix = "s"
        if failure_count > 0:
            if failure_count == 1:
                suffix = ""
            print(failure_count, " failure" + suffix, ": ", failures)
